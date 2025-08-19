from flask import Flask, request, jsonify ,send_from_directory,send_file
from werkzeug.utils import secure_filename
from flasgger import Swagger
from datetime import datetime
from services.speaker_diarization_service import speaker_diarization_service
from services.speaker_identification_service import speaker_identification_service
from services.speech_recognition_service import speech_recognition_service
from services.neural_translation_service import neural_translation_service
from services.file_converter_service import file_converter_service
import os, uuid, zipfile
from werkzeug.utils import secure_filename

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
        "description": "Upload multiple audio files (.wav, .mp3, .ogg, .flac)",
        "version": "1.0.0"
    },
    "basePath": "/",
    "schemes": ["http"],
})

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
@app.route("/", methods=["GET"])
def home():
    return """
    <h2>🎵 Audio Upload API</h2>
    <p>Use <a href='/apidocs'>Swagger UI</a> to test the API.</p>
    <p>Upload endpoint: <code>POST /upload</code></p>
    """



@app.route("/upload", methods=["POST"])
def upload_files():
    if "files" not in request.files:
        return jsonify(error='No "files" field in form-data'), 400

    file_list = request.files.getlist("files")
    if not file_list:
        return jsonify(error="No files supplied"), 400

    file_id = str(uuid.uuid4())
    AUDIO_FILE = os.getenv('AUDIO_FILE', 'audio-file')
    folder_path = os.path.join("uploads", file_id)
    os.makedirs(folder_path, exist_ok=True)

    for uploaded_file in file_list:
        if uploaded_file.filename == "":
            continue
        if not allowed_file(uploaded_file.filename):
            return jsonify(error=f"File type not allowed: {uploaded_file.filename}"), 400

        original_ext = os.path.splitext(uploaded_file.filename)[1].lower()
        final_filename = f"{AUDIO_FILE}{original_ext}"
        local_path = os.path.join(folder_path, secure_filename(final_filename))
        
        uploaded_file.save(local_path)

        # Processing services (jo aap already kar rahe ho)
        speaker_diarization_service(folder_path, final_filename)
        speaker_identification_service(folder_path, final_filename)
        speech_recognition_service(folder_path)
        neural_translation_service(folder_path)
        file_converter_service(folder_path)

    # Output directory jahan processed files hote hain
    output_dir = os.path.join(folder_path, "converted_files")

    # ZIP file banani
    zip_filename = os.path.join(folder_path, "converted_files.zip")
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        for root, _, files in os.walk(output_dir):
            for file in files:
                filepath = os.path.join(root, file)
                zipf.write(filepath, arcname=file)

    # Ab ZIP ko directly download kara do
    return send_file(zip_filename, as_attachment=True, download_name="converted_files.zip")

@app.route('/download/<file_id>/<filename>')
def download_file(file_id, filename):
    """
    Download converted files
    ---
    tags:
      - Download
    parameters:
      - name: file_id
        in: path
        type: string
        required: true
        description: The file ID from upload response
      - name: filename
        in: path
        type: string
        required: true
        description: The filename to download (asr.trn, nmt.txt, sid.csv, sd.csv, lid.csv)
    responses:
      200:
        description: File download
      404:
        description: File not found
    """
    folder_path = os.path.join("uploads", file_id, "converted_files")
    try:
        return send_from_directory(
            directory=folder_path,
            path=filename,
            as_attachment=True
        )
    except FileNotFoundError:
        return jsonify(error="File not found"), 404
    
@app.errorhandler(413)
def too_large(_e):
    return jsonify(error="Request payload too large", max_bytes=MAX_CONTENT_LENGTH), 413

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000, debug=True)
