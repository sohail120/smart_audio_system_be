from pyannote.audio import Pipeline
import os
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
from pydub import AudioSegment
import torch
import json  # Add this at the top
from utils import load_files, save_files


def speaker_diarization_service(file_id: str) -> int:
    """Count the number of unique speakers in an audio file and save results as JSON."""
    files = load_files()
    print("speaker_diarization_service---------------- START")
    # ENV 
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    DIARIZATION_FILE = os.getenv('DIARIZATION_FILE', 'audio-file.rttm')
    UPLOAD_CROPPED_SEGMENTS_FOLDER = os.getenv('UPLOAD_CROPPED_SEGMENTS_FOLDER', 'cropped_segments')
    HF_TOKEN = os.getenv('HF_TOKEN', 'HF_TOKEN')

    # fine index
    file_index = next((i for i, f in enumerate(files) if f['id'] == file_id), None)
    print("files",files)
    if file_index is None:
            print('File not found')

    # Paths
    rttm_file = f'{UPLOAD_FOLDER}/{file_id}/{DIARIZATION_FILE}'
    cropped_file_folder = f'{UPLOAD_FOLDER}\{file_id}\{UPLOAD_CROPPED_SEGMENTS_FOLDER}'
    cropped_file_file = f'{UPLOAD_FOLDER}/{file_id}/{UPLOAD_CROPPED_SEGMENTS_FOLDER}/index.json'
    # audio_file_path = f'{UPLOAD_FOLDER}/{file_id}{files[file_index]['final_filename']}'
    audio_file_path = os.path.join(f'{UPLOAD_FOLDER}/{file_id}/',files[file_index]['filename'])
   # cropped_file_folder
    os.makedirs(cropped_file_folder, exist_ok=True)
    if not os.path.isfile(audio_file_path):
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

    try:

        _PIPELINE = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=HF_TOKEN
    )  
        _PIPELINE.to(torch.device("cpu"))  # Ensure CPU usage
        diarization = _PIPELINE(audio_file_path)
        audio = AudioSegment.from_file(audio_file_path)
        speakers = set()
        segments = []
        count=0

        # Save diarization to RTTM format
        with open(rttm_file, "w") as f:
            diarization.write_rttm(f)

        for turn, _, speaker in diarization.itertracks(yield_label=True):
            speakers.add(speaker)
            segments.append({
                "speaker": speaker,
                "start": int(turn.start * 1000),  # seconds to ms
                "end": int(turn.end * 1000)
            })
            start_ms = int(turn.start * 1000)
            end_ms = int(turn.end * 1000)

            cropped = audio[start_ms:end_ms]
            output_path = os.path.join(cropped_file_folder, f"{count}.wav")
            count+=1
            cropped.export(output_path, format="wav")

        # Save JSON
        output_data = {
            "id": file_id,
            "totalSpeakers": len(speakers),
            "segment": segments
        }
        with open(cropped_file_file, "w") as f:
            json.dump(output_data, f, indent=2)

        files[file_index]['status'] = 2
        save_files(files)
        print("speaker_diarization_service---------------- END")
        return segments

    except Exception as e:
        raise RuntimeError(f"Speaker counting failed: {str(e)}")
