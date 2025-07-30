from pyannote.audio import Pipeline
import os
from pydub import AudioSegment
import torch
from typing import Optional
import json  # Add this at the top
from utils import load_files, save_files

# Global cache for pipeline with CPU optimization
_PIPELINE = None




def convert_to_wav(input_path: str, output_path: str = "temp.wav") -> str:
    """Convert audio file to 16kHz mono WAV format using pydub."""
    try:
        audio = AudioSegment.from_file(input_path)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(output_path, format="wav")
        return output_path
    except Exception as e:
        raise RuntimeError(f"Audio conversion failed: {str(e)}")

def initialize_pipeline(hf_token: str) -> Pipeline:
    """Initialize and configure the pyannote pipeline for CPU."""
    print("Initializing pyannote pipeline for CPU...")
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=hf_token
    )
    pipeline.to(torch.device("cpu"))  # Ensure CPU usage
    return pipeline


def speaker_identification_service(file_id: str, HF_TOKEN: str) -> int:
    print(f"Starting speaker identification for file ID: {file_id}-{HF_TOKEN}")
    """Count the number of unique speakers in an audio file and save results as JSON."""
    global _PIPELINE
    files = load_files()
    file_index = next((i for i, f in enumerate(files) if f['id'] == file_id), None)
    if file_index is None:
            print('File not found')
            
    print("audio_file_path",files)
    audio_file_path=files[file_index]['url']

    if not os.path.isfile(audio_file_path):
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
    


    temp_file = None
    try:
        if not audio_file_path.lower().endswith('.wav'):
            print("Converting audio to WAV format...")
            temp_file = "temp_converted.wav"
            audio_file_path = convert_to_wav(audio_file_path, temp_file)

        if _PIPELINE is None:
            _PIPELINE = initialize_pipeline(HF_TOKEN)

        print("Running speaker diarization...")
        diarization = _PIPELINE(audio_file_path)

        # Collect speaker segments
        speakers = set()
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            speakers.add(speaker)
            segments.append({
                "speaker": speaker,
                "start": int(turn.start * 1000),  # seconds to ms
                "end": int(turn.end * 1000)
            })
            print(f"Speaker {speaker}: {turn.start:.1f}s - {turn.end:.1f}s")
        # Save JSON
        output_data = {
            "id": file_id,
            "totalSpeakers": len(speakers),
            "segment": segments
        }
        with open(f'uploads/diarization-{file_id}.json', "w") as f:
            json.dump(output_data, f, indent=2)
        files[file_index]['status'] = 2
        save_files(files)
        return "ok"

    except Exception as e:
        raise RuntimeError(f"Speaker counting failed: {str(e)}")

    finally:
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)

