import whisper

model = whisper.load_model("turbo")
result = model.transcribe("s2.wav")
print(result["text"])