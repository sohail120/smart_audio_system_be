import os
import numpy as np
import torch
import torchaudio
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
from speechbrain.inference.speaker import EncoderClassifier
from scipy.spatial.distance import cosine
from utils import load_files ,save_files ,load_files 


# ===== Embedding Helpers =====
def normalize_embedding(embedding: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(embedding)
    if norm == 0 or np.isnan(norm):
        return embedding
    return embedding / norm

def load_rttm_segments(rttm_path: str):
    """
    Reads RTTM file and returns list of (start, end, speaker_id).
    """
    segments = []
    if not os.path.exists(rttm_path):
        raise FileNotFoundError(f"RTTM file not found: {rttm_path}")
    with open(rttm_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 8 or parts[0] != "SPEAKER":
                continue
            start = float(parts[3])
            duration = float(parts[4])
            end = start + duration
            speaker_id = parts[7]
            segments.append((start, end, speaker_id))
    return segments

def _prepare_waveform_mono(waveform: torch.Tensor) -> torch.Tensor:
    # waveform shape from torchaudio.load is (channels, samples)
    if waveform.dim() == 1:
        waveform = waveform.unsqueeze(0)
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)
    # normalize audio to -1..1 (avoid division by zero)
    max_val = waveform.abs().max()
    if max_val > 0:
        waveform = waveform / max_val
    return waveform  # shape (1, samples)

# ===== Embedding extraction using SpeechBrain EncoderClassifier =====
def _load_speechbrain_encoder(hf_token: str, device: str = "cpu", savedir: str = "pretrained_models/spkrec-ecapa-voxceleb"):
    """
    Load (or reuse) a speechbrain EncoderClassifier for speaker embeddings.
    """
    run_opts = {"device": device}
    try:
        encoder = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            # run_opts=run_opts,
            # savedir="pretrained_models/spkrec-ecapa-voxceleb,
            use_auth_token=hf_token
        )
    except TypeError:
        # Some older versions might not accept use_auth_token kw; try without it
        encoder = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            run_opts=run_opts,
            savedir=savedir
        )
    return encoder

def extract_averaged_embeddings(audio_file_path: str, rttm_file: str, hf_token: str, min_duration: float = 0.5, device: str = "cpu") -> dict:
    """
    Extract averaged embeddings per speaker from diarized file.
    Returns dict: { speaker_id: [embedding_list] } where embedding_list is a Python list (JSON serializable).
    """
    segments = load_rttm_segments(rttm_file)
    encoder = _load_speechbrain_encoder(hf_token, device=device)

    waveform, sample_rate = torchaudio.load(audio_file_path)
    waveform = _prepare_waveform_mono(waveform)  # (1, samples)
    samples = waveform.shape[1]

    speaker_embeddings = {}
    for start, end, speaker in segments:
        if (end - start) < min_duration:
            continue
        s_idx = int(max(0, np.floor(start * sample_rate)))
        e_idx = int(min(samples, np.ceil(end * sample_rate)))
        if e_idx <= s_idx:
            continue
        segment_waveform = waveform[:, s_idx:e_idx]  # (1, seg_samples)
        # speechbrain expects (batch, n_samples) as float tensor
        seg_tensor = segment_waveform.squeeze(0).unsqueeze(0)  # (1, n_samples)
        with torch.no_grad():
            try:
                emb = encoder.encode_batch(seg_tensor)  # returns torch.Tensor
            except Exception as exc:
                # fallback: try giving raw tensor on CPU
                emb = encoder.encode_batch(seg_tensor.cpu())
        emb_np = emb.squeeze(0).cpu().numpy()
        emb_np = normalize_embedding(emb_np)
        speaker_embeddings.setdefault(speaker, []).append(emb_np)

    # Average per speaker and normalize
    averaged_embeddings = {}
    for spk, embs in speaker_embeddings.items():
        if len(embs) == 0:
            continue
        stacked = np.vstack(embs)
        mean_emb = np.mean(stacked, axis=0)
        mean_emb = normalize_embedding(mean_emb)
        averaged_embeddings[spk] = mean_emb.tolist()

    return averaged_embeddings

# ===== Matching Logic =====
def match_segments_to_enrolment(audio_file_path: str, rttm_file: str, hf_token: str, enrolment_data: dict, min_duration: float = 0.5, similarity_threshold: float = 0.8, device: str = "cpu"):
    """
    Match each diarized segment in a file to known enrolment speakers.
    enrolment_data: { speaker_id: [embedding_list] } (embedding_list stored as plain lists)
    """
    if not enrolment_data:
        raise ValueError("Enrolment data is empty or None.")

    # convert enrolment embeddings to numpy arrays and normalize
    enrolment_np = {}
    for speaker_id, emb_list in enrolment_data.items():
        emb_arr = np.array(emb_list, dtype=float)
        emb_arr = normalize_embedding(emb_arr)
        enrolment_np[speaker_id] = emb_arr

    segments = load_rttm_segments(rttm_file)
    encoder = _load_speechbrain_encoder(hf_token, device=device)

    waveform, sample_rate = torchaudio.load(audio_file_path)
    waveform = _prepare_waveform_mono(waveform)
    samples = waveform.shape[1]

    results = []
    for start, end, _ in segments:
        if (end - start) < min_duration:
            continue
        s_idx = int(max(0, np.floor(start * sample_rate)))
        e_idx = int(min(samples, np.ceil(end * sample_rate)))
        if e_idx <= s_idx:
            continue
        segment_waveform = waveform[:, s_idx:e_idx]
        seg_tensor = segment_waveform.squeeze(0).unsqueeze(0)
        with torch.no_grad():
            try:
                emb = encoder.encode_batch(seg_tensor)
            except Exception:
                emb = encoder.encode_batch(seg_tensor.cpu())
        emb_np = emb.squeeze(0).cpu().numpy()
        emb_np = normalize_embedding(emb_np)

        best_match = None
        best_score = float("inf")
        for speaker_id, speaker_emb in enrolment_np.items():
            # cosine returns distance in [0, 2] for normalized vectors; lower is better
            try:
                score = cosine(speaker_emb, emb_np)
            except Exception:
                # fallback to large score if something wrong
                score = float("inf")
            if score < best_score:
                best_score = score
                best_match = speaker_id

        similarity = 1.0 - best_score  # approximate; for normalized vectors cos distance ~ (1-cos)
        matched = similarity >= similarity_threshold
        results.append({
            "start": float(start),
            "end": float(end),
            "best_match": best_match,
            "similarity": float(similarity),
            "matched": bool(matched)
        })
        if matched:
            print(f"[MATCH] {start:.2f}-{end:.2f}s → '{best_match}' (similarity {similarity:.2f})")
        else:
            print(f"[NO MATCH] {start:.2f}-{end:.2f}s → best '{best_match}' ({similarity:.2f})")
    return results

# ===== Main Service =====
def speaker_identification_service(folder_path: str,final_filename:str):
    print("speaker_identification_service---------------- START")

    HF_TOKEN = os.getenv('HF_TOKEN', None)
    DIARIZATION_FILE = os.getenv('DIARIZATION_FILE', 'audio-file.rttm')
    ENROLMENT_FILE = os.getenv('ENROLMENT_FILE', f"{folder_path}/enrolment.json")
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

    rttm_file = f"{folder_path}/{DIARIZATION_FILE}"
    audio_file_path = os.path.join(f"{folder_path}/", final_filename)

    enrolment_data = load_files(ENROLMENT_FILE)
    if not enrolment_data:
        enrolment_data = None
        
    if enrolment_data is None:
        print("[INFO] No enrolment data found — extracting embeddings to create enrolment.")
        embeddings = extract_averaged_embeddings(audio_file_path, rttm_file, HF_TOKEN, device=DEVICE)
        save_files(embeddings, ENROLMENT_FILE)
        print("[INFO] Enrolment data saved. Future runs will compare to this.")
    else:
        print("[INFO] Matching segments to enrolment speakers...")
        match_segments_to_enrolment(audio_file_path, rttm_file, HF_TOKEN, enrolment_data, device=DEVICE)
        print("[INFO] Matching complete.")
    print("speaker_identification_service---------------- END")
