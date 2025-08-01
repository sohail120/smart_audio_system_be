from transformers import pipeline

# Load translation pipeline (many language pairs available)
translator = pipeline("translation", model="Helsinki-NLP/opus-mt-mul-en")

text_to_translate = "Bonjour le monde"  # Example French text
translation = translator(text_to_translate)

print(translation[0]['translation_text'])


# neural_translation_service