from services.speaker_diarization_service import speaker_diarization_service
from services.speaker_identification_service import speaker_identification_service
from services.speech_recognition_service import speech_recognition_service
from services.neural_translation_service import neural_translation_service
from services.file_converter_service import file_converter_service


def main_thread(id):
    print("main_thread ---------------- START")
    speaker_diarization_service(id)
    speaker_identification_service(id)
    speech_recognition_service(id)
    neural_translation_service(id)
    file_converter_service(id)
    
    print("main_thread ---------------- END")