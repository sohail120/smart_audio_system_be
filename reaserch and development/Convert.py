from pydub import AudioSegment

def convert_mp3_to_wav(mp3_path: str, wav_path: str = "temp.wav"):
    """Convert MP3 to WAV for better compatibility."""
    audio = AudioSegment.from_mp3(mp3_path)
    audio.export(wav_path, format="wav")
    return wav_path

# Usage:
wav_file = convert_mp3_to_wav("audio-sample.mp3")
num_speakers = count_speakers(wav_file, HF_TOKEN)
os.remove(wav_file)  # Clean up