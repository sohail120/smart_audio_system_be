from pyannote.audio import Pipeline
import os
from pydub import AudioSegment
import json

# Global cache for pipeline
_PIPELINE = None
output_folder = "uploads"
os.makedirs(output_folder, exist_ok=True)

# Load audio

# Prepare result list
results = []


def convert_mp3_to_wav(mp3_path: str, wav_path: str = "temp.wav"):
    """Convert MP3 to WAV using pydub."""
    audio = AudioSegment.from_mp3(mp3_path)
    audio.export(wav_path, format="wav")
    return wav_path

def count_speakers(audio_file_path: str, hf_token: str) -> int:
    global _PIPELINE

    if not os.path.isfile(audio_file_path):
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

    if audio_file_path.endswith(".mp3"):
        print("Converting MP3 to WAV...")
        audio_file_path = convert_mp3_to_wav(audio_file_path)

    try:
        if _PIPELINE is None:
            print("Loading pyannote speaker diarization pipeline...")
            _PIPELINE = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=hf_token
            )

        print("Running diarization...")
        diarization = _PIPELINE(audio_file_path)
        audio = AudioSegment.from_wav(audio_file_path)

        speakers = set()
        for turn, _, speaker in diarization.itertracks(yield_label=True):
             start_ms = int(turn.start * 1000)
             end_ms = int(turn.end * 1000)
             segment = audio[start_ms:end_ms]

             # Create unique filename
             filename = f"{speaker}_{start_ms}_{end_ms}.wav"
             filepath = os.path.join(output_folder, filename)
    
             # Export segment
             segment.export(filepath, format="wav")
             # Append metadata
             results.append({
             "filename": filename,
             "speaker": speaker,
             "start": float(f"{turn.start:.2f}"),
             "end": float(f"{turn.end:.2f}")
             })
             print(f"Speaker {speaker} spoke from {turn.start:.1f}s to {turn.end:.1f}s")
             speakers.add(speaker)

        return len(speakers)

    except Exception as e:
        raise RuntimeError(f"Diarization failed: {str(e)}")


if __name__ == "__main__":
    HF_TOKEN = ""
    AUDIO_PATH = "s2.wav"  # or "sample.wav"

    try:
        count = count_speakers(AUDIO_PATH, HF_TOKEN)
        # Save metadata JSON
        with open(os.path.join(output_folder, "segments.json"), "w") as f:
          json.dump(results, f, indent=2)

        print(f"Detected number of speakers: {count}")
    except Exception as e:
        print("Error:", e)















# Load pipeline once

