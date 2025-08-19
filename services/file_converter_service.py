import json
import csv
import os

def file_converter_service(
  folder_path: str,
):
    TRANSCRIPTION = os.getenv('TRANSCRIPTION', "transcription.json")
    NEURAL_TRANSLATION = os.getenv('NEURAL_TRANSLATION', "neural_translation.json")

    transcription_path = f'{folder_path}/{TRANSCRIPTION}'
    translation_path = f'{folder_path}/{NEURAL_TRANSLATION}'
    output_dir = f'{folder_path}/converted_files'
    os.makedirs(output_dir, exist_ok=True)
    """
    Converts transcription and translation JSON files into various CSV and text formats.
    """
    try:
        with open(transcription_path, "r", encoding="utf-8") as f:
            transcription = json.load(f)
        with open(translation_path, "r", encoding="utf-8") as f:
            translation = json.load(f)
    except Exception as e:
        print(f"Error loading input files: {e}")
        return

    # SID (Speaker ID CSV)
    sid_path = os.path.join(output_dir, "sid.csv")
    with open(sid_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["file", "speaker_id", "confidence", "start", "end"])
        for seg in transcription["segments"]["segment"]:
            writer.writerow(["audio-file", seg.get("speaker", ""), 1.0, seg.get("start", ""), seg.get("end", "")])

    # SD (Speaker Diarization CSV)
    sd_path = os.path.join(output_dir, "sd.csv")
    with open(sd_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["file", "speaker_label", "confidence", "start", "end"])
        for seg in transcription["segments"]["segment"]:
            writer.writerow(["audio-file", seg.get("speaker", ""), 1.0, seg.get("start", ""), seg.get("end", "")])

    # LID (Language ID CSV)
    lid_path = os.path.join(output_dir, "lid.csv")
    with open(lid_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["file", "language", "confidence", "start", "end"])
        for seg in transcription["segments"]["segment"]:
            writer.writerow(["audio-file", seg.get("language", ""), 1.0, seg.get("start", ""), seg.get("end", "")])

    # ASR (Transcription TRN format)
    asr_path = os.path.join(output_dir, "asr.trn")
    with open(asr_path, "w", encoding="utf-8") as f:
        for seg in transcription["segments"]["segment"]:
            f.write(f"{seg.get('start', '')}-{seg.get('end', '')} {seg.get('transcript', '')}\n")

    # NMT (Translation TXT format)
    nmt_path = os.path.join(output_dir, "nmt.txt")
    with open(nmt_path, "w", encoding="utf-8") as f:
        for seg in translation["segments"]["segment"]:
            f.write(f"{seg.get('start', '')}-{seg.get('end', '')} {seg.get('translated_text', '')}\n")
