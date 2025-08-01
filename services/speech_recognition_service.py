import whisper
import os
import json
from utils import load_files, save_files

def speech_recognition_service(file_id: str) -> str:
    """
    Transcribes all cropped speaker segments using OpenAI Whisper
    and saves the results in a new JSON file.
    """
    print("Transcription service started for file ID:", file_id)

    # Load files metadata
    files = load_files()
    file_index = next((i for i, f in enumerate(files) if f['id'] == file_id), None)
    if file_index is None:
        raise ValueError(f"No entry found for file ID: {file_id}")

    # Load speaker diarization data
    diarization_path = f"uploads/diarization-{file_id}.json"
    if not os.path.exists(diarization_path):
        raise FileNotFoundError(f"Diarization file not found: {diarization_path}")
    
    with open(diarization_path, 'r') as f:
        speaker_data = json.load(f)

    segments = speaker_data.get("segment", [])
    if not segments:
        raise ValueError("No segments found in diarization JSON.")

    # Load Whisper model (adjust size as needed: base/small/medium/large)
    model = whisper.load_model("medium")

    # Transcribe each segment
    output_dir = "cropped_segments"
    for i, segment in enumerate(segments):

        speaker = segment["speaker"]
        cropped_audio_path = os.path.join(output_dir, f"{file_id}_{speaker}_{i+1}.wav")
        if not os.path.exists(cropped_audio_path):
            print(f"Skipped missing audio segment: {cropped_audio_path}")
            segment["transcript"] = ""
            continue

        print(f"Transcribing: {cropped_audio_path}")
        result = model.transcribe(cropped_audio_path)
        print(f"Transcription result for segment {i+1}: {result}")
        segment["transcript"] = result.get("text", "").strip()
        segment["language"] = result.get("language", "").strip()


    # Save transcript-augmented JSON
    transcription_output_path = f"uploads/transcription-{file_id}.json"
    with open(transcription_output_path, 'w') as f:
        json.dump(speaker_data, f, indent=2)
    print(f"Transcription saved to: {transcription_output_path}")

    # Update file status
    files[file_index]['status'] = 6
    save_files(files)

    return "ok"


# # Replace with a valid file ID from your `files.json`
# file_id = "7b4d034c-9a47-4912-bc1e-b25c2340388d"

# # Call the transcription service
# response = speech_recognition_service(file_id)

# # Print the response
# print(response)