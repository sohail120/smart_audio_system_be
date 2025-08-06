import csv
from pyannote.audio import Pipeline
from typing import List
import os

pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token="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"
            )
class SpeakerSegment:
    def __init__(self, audio_file: str, speaker_id: str, confidence: float, start: float, end: float):
        self.audio_file = os.path.basename(audio_file)
        self.speaker_id = speaker_id
        self.confidence = confidence
        self.start = start
        self.end = end

def analyze_audio_file(audio_path: str) -> List[SpeakerSegment]:
    """Analyze an audio file and return speaker segments"""
    try:
        # Apply the pipeline to the audio file
        diarization = pipeline(audio_path)
        
        segments = []
        
        # Extract speaker segments with confidence scores
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append(
                SpeakerSegment(
                    audio_file=audio_path,
                    speaker_id=speaker,
                    confidence=1.0,  # pyannote doesn't provide confidence scores directly
                    start=round(turn.start, 2),
                    end=round(turn.end, 2)
                )
            )
        
        return segments
    
    except Exception as e:
        print(f"Error processing {audio_path}: {str(e)}")
        return []

def export_to_csv(segments: List[SpeakerSegment], output_path: str):
    """Export speaker segments to CSV file"""
    with open(output_path, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Audio File Name",
            "speaker ID",
            "confidence score (%)",
            "start TS",
            "end TS"
        ])
        
        for segment in segments:
            writer.writerow([
                segment.audio_file,
                segment.speaker_id,
                segment.confidence * 100,  # Convert to percentage
                segment.start,
                segment.end
            ])

def process_audio_files(input_files: List[str], output_csv: str):
    """Process multiple audio files and save results to CSV"""
    all_segments = []
    
    for audio_file in input_files:
        print(f"Processing {audio_file}...")
        segments = analyze_audio_file(audio_file)
        all_segments.extend(segments)
    
    export_to_csv(all_segments, output_csv)
    print(f"Results saved to {output_csv}")

if __name__ == "__main__":
    # Example usage
    audio_files = [
        "output_cropped.mp3",
        # "audio_samples/interview2.mp3"
    ]
    
    output_file = "speaker_identification_results.csv"
    
    process_audio_files(audio_files, output_file)