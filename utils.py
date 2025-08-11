import os
import json  # Ad
import os
import json
from config import  ALLOWED_EXTENSIONS ,JSON_STORAGE
from pydub import AudioSegment
import shutil


# Helper Functions
def load_files(JSON_STORAGE=JSON_STORAGE):
    if not os.path.exists(JSON_STORAGE):
        return []
    try:
        with open(JSON_STORAGE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_files(files,JSON_STORAGE=JSON_STORAGE):
    with open(JSON_STORAGE, 'w') as f:
        json.dump(files, f, indent=2)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def convert_to_wav(input_path: str, output_path: str = "temp.wav") -> str:
    """Convert audio file to 16kHz mono WAV format using pydub."""
    try:
        audio = AudioSegment.from_file(input_path)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(output_path, format="wav")
        return output_path
    except Exception as e:
        raise RuntimeError(f"Audio conversion failed: {str(e)}")
    



def merge_rttm(file1_path, file2_path, output_path):
    # Case 1: First file doesn't exist -> just copy the second one
    if not os.path.exists(file1_path):
        if os.path.exists(file2_path):
            shutil.copy(file2_path, output_path)
            print(f"{file1_path} not found. Created {output_path} from {file2_path}")
        else:
            print("Neither RTTM file exists. Nothing to merge.")
        return

    # Case 2: First file exists -> merge normally
    lines = []

    # Read file1
    with open(file1_path, 'r') as f1:
        for line in f1:
            if line.strip():
                lines.append(line.strip())

    # Read file2
    if os.path.exists(file2_path):
        with open(file2_path, 'r') as f2:
            for line in f2:
                if line.strip():
                    lines.append(line.strip())

    # Sort lines by start time (column 4 in RTTM, index 3)
    lines.sort(key=lambda x: float(x.split()[3]))

    # Write merged file
    with open(output_path, 'w') as out:
        for line in lines:
            out.write(line + '\n')

    print(f"Merged RTTM saved to: {output_path}")


