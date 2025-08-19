from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from flasgger import Swagger
from services.speaker_diarization_service import speaker_diarization_service
from services.speaker_identification_service import speaker_identification_service
from services.speech_recognition_service import speech_recognition_service
from services.neural_translation_service import neural_translation_service
from services.file_converter_service import file_converter_service
import os, uuid, zipfile

# --- Config ---
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
ALLOWED_EXTENSIONS = {"wav", "mp3", "ogg", "flac"}  # 🎵 only audio files
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB total request limit

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR

os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Swagger setup ---
swagger = Swagger(app, template={
    "swagger": "2.0",
    "info": {
        "title": "Audio Upload API",
        "description": "Upload multiple audio files (.wav, .mp3, .ogg, .flac) "
                       "and download a processed ZIP with diarization, identification, "
                       "transcription & translation.",
        "version": "1.0.0"
    },
    "basePath": "/",
    "schemes": ["http"],
})


# --- Helper function ---
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# --- Routes ---
@app.route("/", methods=["GET"])
def home():
    return """
    <h2>🎵 Audio Upload API</h2>
    <p>Use <a href='/apidocs'>Swagger UI</a> to test the API.</p>
    <p>Upload endpoint: <code>POST /upload</code></p>
    """


@app.route("/upload", methods=["POST"])
def upload_file():
    """
    Upload a single audio file
    ---
    tags:
      - Upload
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: Select one audio file (.wav, .mp3, .ogg, .flac)
    responses:
      200:
        description: ZIP file with processed outputs
        schema:
          type: file
      400:
        description: Invalid request
    """
    if "file" not in request.files:
        return jsonify(error='No "file" field in form-data'), 400

    uploaded_file = request.files["file"]

    if uploaded_file.filename == "":
        return jsonify(error="No file selected"), 400

    if not allowed_file(uploaded_file.filename):
        return jsonify(error=f"File type not allowed: {uploaded_file.filename}"), 400

    file_id = str(uuid.uuid4())
    AUDIO_FILE = os.getenv('AUDIO_FILE', 'audio-file')
    folder_path = os.path.join("uploads", file_id)
    os.makedirs(folder_path, exist_ok=True)

    # Rename and save
    original_ext = os.path.splitext(uploaded_file.filename)[1].lower()
    final_filename = f"{AUDIO_FILE}{original_ext}"
    local_path = os.path.join(folder_path, secure_filename(final_filename))

    uploaded_file.save(local_path)

    # 🎤 Processing services
    speaker_diarization_service(folder_path, final_filename)
    speaker_identification_service(folder_path, final_filename)
    speech_recognition_service(folder_path)
    neural_translation_service(folder_path)
    file_converter_service(folder_path)

    # Output directory
    output_dir = os.path.join(folder_path, "converted_files")

    # ZIP file
    zip_filename = os.path.join(folder_path, "converted_files.zip")
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        for root, _, files in os.walk(output_dir):
            for file in files:
                filepath = os.path.join(root, file)
                zipf.write(filepath, arcname=file)

    return send_file(zip_filename, as_attachment=True, download_name="converted_files.zip")


@app.errorhandler(413)
def too_large(_e):
    return jsonify(error="Request payload too large", max_bytes=MAX_CONTENT_LENGTH), 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000, debug=True)
