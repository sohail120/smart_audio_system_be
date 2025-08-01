from pydub import AudioSegment
import os

def crop_audio(input_file, output_file, start_time, end_time):
    """
    Crop an audio file between specified start and end times.
    
    Parameters:
        input_file (str): Path to the input audio file
        output_file (str): Path to save the cropped audio file
        start_time (int): Start time in milliseconds
        end_time (int): End time in milliseconds
    """
    try:
        # Load the audio file
        audio = AudioSegment.from_file(input_file)
        
        # Crop the audio
        cropped_audio = audio[start_time:end_time]
        
        # Export the cropped audio
        cropped_audio.export(output_file, format=output_file.split('.')[-1])
        
        print(f"Audio successfully cropped and saved to {output_file}")
        return True
    
    except Exception as e:
        print(f"Error cropping audio: {str(e)}")
        return False


# Example usage:
if __name__ == "__main__":
    # Input file (supports many formats: mp3, wav, ogg, flac, etc.)
    input_file = "king.mp3"
    
    # Output file (format determined by extension)
    output_file = "output_cropped.mp3"
    
    # Time in milliseconds (e.g., 10 seconds to 30 seconds)
    start_time = 0  # 10 seconds
    end_time = 30000    # 30 seconds
    
    crop_audio(input_file, output_file, start_time, end_time)