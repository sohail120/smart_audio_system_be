import json
import os
from pydub import AudioSegment
from utils import load_files, save_files

def speaker_diarization_service(file_id: str) -> list:
    """
    Read speaker diarization data from JSON and crop audio segments.

    Args:
        file_id (str): ID of the file as saved in files.json

    Returns:
        list: List of file paths for cropped audio segments.
    """
    output_dir = "cropped_segments"
    json_path = f"uploads/diarization-{file_id}.json"
    output_files = []

    try:
        files = load_files()
        file_index = next((i for i, f in enumerate(files) if f['id'] == file_id), None)
        if file_index is None:
            raise ValueError(f"File ID '{file_id}' not found in files.json")

        print(f"Processing file ID: {file_id} with index: {file_index}")
        audio_path = files[file_index]['url']

        # Validate file paths
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"JSON not found: {json_path}")
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio not found: {audio_path}")

        # Load JSON data
        with open(json_path, 'r') as f:
            data = json.load(f)

        if "segment" not in data or not data["segment"]:
            raise ValueError("No segments found in the JSON file.")

        # Load full audio once
        audio = AudioSegment.from_file(audio_path)

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Crop each segment
        for i, segment in enumerate(data["segment"]):
            speaker = segment['speaker']
            start_ms = segment['start']
            end_ms = segment['end']

            cropped = audio[start_ms:end_ms]
            output_path = os.path.join(output_dir, f"{data['id']}_{speaker}_{i+1}.wav")
            cropped.export(output_path, format="wav")
            output_files.append(output_path)
            print(f"Cropped: {output_path}")

        print("All segments processed.")
        files[file_index]['status'] = 4
        save_files(files)

    except Exception as e:
        files = load_files()
        file_index = next((i for i, f in enumerate(files) if f['id'] == file_id), None)
        files[file_index]['status'] = 2
        print(f"[ERROR] Failed to process diarization for file ID '{file_id}': {str(e)}")

    return output_files
