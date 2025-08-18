import json
import os
from transformers import pipeline
from tqdm import tqdm

# Cache translation models so they're not reloaded every call
translation_models = {}

def _load_model(lang, hf_token):
    """Lazy-load translation model for given language."""
    model_map = {
        'hi': "Helsinki-NLP/opus-mt-hi-en",
        'ur': "Helsinki-NLP/opus-mt-ur-en",
        'pa': "Helsinki-NLP/opus-mt-pa-en",
        'bn': "Helsinki-NLP/opus-mt-bn-en",
        'default': "Helsinki-NLP/opus-mt-mul-en"
    }

    model_name = model_map.get(lang, model_map['default'])

    if model_name not in translation_models:
        print(f"🔄 Loading model for '{lang}' → {model_name}")
        translation_models[model_name] = pipeline(
            "translation",
            model=model_name,
            token=hf_token  # use_auth_token is deprecated
        )

    return translation_models[model_name]

def _ms_to_srt(milliseconds):
    """Convert milliseconds to SRT time format (HH:MM:SS,mmm)"""
    seconds, ms = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"

def neural_translation_service(file_id: str):
    print("neural_translation_service ---------------- START")
    """Translates transcription JSON to English and saves translated JSON."""
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    TRANSCRIPTION = os.getenv('TRANSCRIPTION', "transcription.json")
    NEURAL_TRANSLATION = os.getenv('NEURAL_TRANSLATION', "neural_translation.json")
    HF_TOKEN = os.getenv('HF_TOKEN', None)

    transcription_path = f'{UPLOAD_FOLDER}/{file_id}/{TRANSCRIPTION}'
    translation_output_path = f'{UPLOAD_FOLDER}/{file_id}/{NEURAL_TRANSLATION}'

    if not os.path.exists(transcription_path):
        raise FileNotFoundError(f"Transcription file not found: {transcription_path}")

    # Load transcription JSON
    with open(transcription_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Translate each segment
    for segment in tqdm(data.get('segments', {}).get('segment', []), desc="Translating segments"):
        lang = segment.get('language', 'default')
        text = segment.get('transcript', '')

        if not text.strip():
            segment['translated_text'] = ''
            continue

        try:
            model = _load_model(lang, HF_TOKEN)
            translated = model(text, max_length=400)[0]['translation_text']
            segment['translated_text'] = translated
        except Exception as e:
            print(f"⚠️ Translation failed for {lang}: {e}")
            try:
                # Retry with default model
                model = _load_model('default', HF_TOKEN)
                translated = model(text, max_length=400)[0]['translation_text']
                segment['translated_text'] = translated
            except Exception as e2:
                print(f"❌ Fallback translation also failed: {e2}")
                segment['translated_text'] = "[TRANSLATION FAILED]"

    # Save translated JSON
    with open(translation_output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("neural_translation_service ---------------- END")