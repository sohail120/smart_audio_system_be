import whisper
import os
import json
from utils import load_files, save_files

def speech_recognition_service(file_id: str) -> str:
    """
    Transcribes all cropped speaker segments using OpenAI Whisper,
    saves the results in both JSON and TRN format.
    """
    print("speech_recognition_service ---------------- START")

    # Load files metadata
    files = load_files()
    file_index = next((i for i, f in enumerate(files) if f['id'] == file_id), None)
    if file_index is None:
        raise ValueError(f"No entry found for file ID: {file_id}")
    
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    TRANSCRIPTION = os.getenv('TRANSCRIPTION', "transcription.json")
    UPLOAD_CROPPED_SEGMENTS_FOLDER = os.getenv('UPLOAD_CROPPED_SEGMENTS_FOLDER', 'uploads')

    output_dir = f'{UPLOAD_FOLDER}\{file_id}\{UPLOAD_CROPPED_SEGMENTS_FOLDER}'
    transcription_output_path = f'{UPLOAD_FOLDER}/{file_id}/{TRANSCRIPTION}'
    segment_path= f'{UPLOAD_FOLDER}/{file_id}/{UPLOAD_CROPPED_SEGMENTS_FOLDER}/index.json'
    segments = load_files(segment_path)
    print("segments", segments['segment'])
    if not segments['segment']:
        raise ValueError("No segments found for transcription.")

    # Load Whisper model
    model = whisper.load_model("medium")


    for i, segment in enumerate(segments['segment']):
        # speaker = segment["speaker"]
        cropped_audio_path = os.path.join(output_dir, f"{i}.wav")

        if not os.path.exists(cropped_audio_path):
            print(f"Skipped missing audio segment: {cropped_audio_path}")
            segment["transcript"] = ""
            continue

        print(f"Transcribing: {cropped_audio_path}")
        result = model.transcribe(cropped_audio_path)

        transcript = result.get("text", "").strip()
        language = result.get("language", "").strip()

        segment["transcript"] = transcript
        segment["language"] = language


    with open(transcription_output_path, 'w') as f:
        json.dump({"segments": segments}, f, indent=2)
    print(f"Transcription JSON saved to: {transcription_output_path}")

    # Update status
    files[file_index]['status'] = 6
    save_files(files)
    print("speech_recognition_service ---------------- START")

    return "ok"
