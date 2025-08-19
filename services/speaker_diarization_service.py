from pyannote.audio import Pipeline
import os
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
from pydub import AudioSegment
import torch
import json  # Add this at the top
from utils import load_files, save_files


def speaker_diarization_service(folderPath: str,filename:str) -> int:
    """Count the number of unique speakers in an audio file and save results as JSON."""
    print("speaker_diarization_service---------------- START")
    # ENV 
    DIARIZATION_FILE = os.getenv('DIARIZATION_FILE', 'audio-file.rttm')
    UPLOAD_CROPPED_SEGMENTS_FOLDER = os.getenv('UPLOAD_CROPPED_SEGMENTS_FOLDER', 'cropped_segments')
    HF_TOKEN = os.getenv('HF_TOKEN', 'HF_TOKEN')

    # Paths
    rttm_file = f'{folderPath}/{DIARIZATION_FILE}'
    cropped_file_folder = f'{folderPath}\{UPLOAD_CROPPED_SEGMENTS_FOLDER}'
    cropped_file_file = f'{folderPath}/{UPLOAD_CROPPED_SEGMENTS_FOLDER}/index.json'
    audio_file_path = os.path.join(f'{folderPath}/',filename)

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
            "totalSpeakers": len(speakers),
            "segment": segments
        }
        with open(cropped_file_file, "w") as f:
            json.dump(output_data, f, indent=2)

        print("speaker_diarization_service---------------- END")
        return segments

    except Exception as e:
        raise RuntimeError(f"Speaker counting failed: {str(e)}")
