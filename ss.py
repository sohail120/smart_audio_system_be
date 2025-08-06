import csv
import torchaudio
from speechbrain.pretrained import VAD, EncoderClassifier
from speechbrain.utils.metric_stats import metric_stats
import numpy as np
from scipy.io import wavfile
import librosa
import os

# Load pre-trained models
vad = VAD.from_hparams(source="speechbrain/vad-crdnn-libriparty")
classifier = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb")

# Enrollment data (simulated: replace with actual enrollment audio files)
enrollment_files = {
    "Priya": "enrollment_priya.wav",  # Path to Priya's enrollment audio
    "Raj": "enrollment_raj.wav"       # Path to Raj's enrollment audio
}
enrollment_embeddings = {}
for speaker_id, file_path in enrollment_files.items():
    audio, sr = torchaudio.load(file_path)
    embedding = classifier.encode_batch(audio)
    enrollment_embeddings[speaker_id] = embedding.squeeze()

def process_audio(audio_file, evaluation_id="01"):
    # Load and preprocess audio
    audio, sr = librosa.load(audio_file, sr=16000)  # Resample to 16kHz
    wavfile.write(f"temp_{audio_file}", 16000, (audio * 32768).astype(np.int16))  # Save temp WAV

    # Step 1: Voice Activity Detection (VAD)
    boundaries = vad.get_speech_segments(f"temp_{audio_file}", large_chunk_size=30, small_chunk_size=0.5)
    segments = []
    for start, end in boundaries:
        if end - start >= 0.5:  # Ignore pauses ≤ 500 ms
            segments.append((start, end))

    # Step 2: Speaker Diarization (SD)
    sd_results = []
    speaker_count = 0
    prev_speaker = None
    speaker_labels = {}
    segment_embeddings = []

    for start, end in segments:
        # Extract audio segment
        segment_audio = audio[int(start * 16000):int(end * 16000)]
        wavfile.write("temp_segment.wav", 16000, (segment_audio * 32768).astype(np.int16))
        segment_tensor, _ = torchaudio.load("temp_segment.wav")
        
        # Get embedding for diarization
        embedding = classifier.encode_batch(segment_tensor).squeeze()
        segment_embeddings.append(embedding)

        # Simple clustering for diarization (compare with previous segments)
        if prev_speaker is None:
            speaker_count += 1
            speaker_label = f"speaker{speaker_count}"
            speaker_labels[(start, end)] = speaker_label
            prev_speaker = embedding
        else:
            similarity = metric_stats.cosine_similarity(embedding, prev_speaker)
            if similarity > 0.7:  # Threshold for same speaker
                speaker_labels[(start, end)] = speaker_label
            else:
                speaker_count += 1
                speaker_label = f"speaker{speaker_count}"
                speaker_labels[(start, end)] = speaker_label
                prev_speaker = embedding

        sd_results.append([audio_file, speaker_label, 95, start, end])  # Fixed confidence for simplicity

    # Step 3: Speaker Identification (SID)
    sid_results = []
    for (start, end), embedding in zip(segments, segment_embeddings):
        # Compare with enrollment embeddings
        similarities = [metric_stats.cosine_similarity(embedding, enroll_emb) for enroll_emb in enrollment_embeddings.values()]
        max_sim_idx = np.argmax(similarities)
        speaker_id = list(enrollment_embeddings.keys())[max_sim_idx]
        confidence = similarities[max_sim_idx] * 100  # Convert to percentage
        sid_results.append([audio_file, speaker_id, round(confidence, 2), start, end])

    # Step 4: Save results in CSV format
    with open(f"SID_{evaluation_id}.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Audio File Name", "Speaker ID", "Confidence Score (%)", "Start TS", "End TS"])
        writer.writerows(sid_results)

    with open(f"SD_{evaluation_id}.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Audio File Name", "Speaker", "Confidence Score (%)", "Start TS", "End TS"])
        writer.writerows(sd_results)

    # Clean up temporary files
    os.remove(f"temp_{audio_file}")
    if os.path.exists("temp_segment.wav"):
        os.remove("temp_segment.wav")

# Example usage
if __name__ == "__main__":
    audio_file = "meeting.wav"  # Replace with your audio file (WAV, MP3, OGG, FLAC)
    process_audio(audio_file, evaluation_id="01")