import os
from moviepy import VideoFileClip
from pydub import AudioSegment
import numpy as np
import soundfile as sf
from scipy.signal import resample

# Configurations
SAMPLE_RATES = [8000, 16000, 22050, 44100, 48000]
BIT_DEPTHS = [8, 16, 24, 32]
FORMATS = ["wav", "mp3", "ogg", "flac"]
SNR_VALUES = [-5, 0, 5, 10, 15, 20]

def extract_audio_from_mp4(mp4_path, output_wav="temp.wav"):
    print(f"[INFO] Extracting audio from: {mp4_path}")
    video = VideoFileClip(mp4_path)
    video.audio.write_audiofile(output_wav, fps=44100)
    return output_wav


input_mp4 = "jethalal.mp4"  # Replace with your input file
extract_audio_from_mp4(input_mp4)
