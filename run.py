import os
import uuid
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_restx import Api, Resource, fields, Namespace
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from flask_cors import CORS
import threading
from services.speech_recognition_service import speech_recognition_service
from services.speaker_identification_service import speaker_identification_service
from services.speaker_diarization_service import speaker_diarization_service



# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'pdf', 'docx', 'jpg', 'png'}
JSON_STORAGE = 'files.json'
HF_TOKEN = "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"
AUDIO_PATH = "s2.wav"  # or "sample.wav"

# Initialize Flask app
app = Flask(__name__)
CORS(app) 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB/

# Create required directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Flask-RESTX setup
api = Api(app, version='1.0', title='File Management API',
          description='A simple CRUD API for managing files with JSON storage')
ns = Namespace('files', description='File operations')
api.add_namespace(ns, path='/files')

# Swagger Models
file_model = ns.model('File', {
    'id': fields.String(readonly=True, description='The file identifier'),
    'name': fields.String(required=True, description='The file name'),
    'createdAt': fields.String(readonly=True, description='Creation timestamp'),
    'status': fields.String(required=True, description='File processing status',
                            enum=['processing', 'completed', 'failed'], default='processing'),
    'url': fields.String(readonly=True, description='Local file path')
})

upload_parser = ns.parser()
upload_parser.add_argument('file', location='files',
                           type=FileStorage, required=True, help='The file to upload')
upload_parser.add_argument('name', location='form', required=True, help='Display name for the file')
upload_parser.add_argument('status', location='form', required=False, help='File processing status')


# Helper Functions
def load_files():
    if not os.path.exists(JSON_STORAGE):
        return []
    try:
        with open(JSON_STORAGE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_files(files):
    with open(JSON_STORAGE, 'w') as f:
        json.dump(files, f, indent=2)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_local_file_path(filename):
    return os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))


# Routes
@ns.route('/')
class FileList(Resource):
    @ns.marshal_list_with(file_model)
    def get(self):
        """List all files"""
        return load_files()

    @ns.expect(upload_parser)
    @ns.marshal_with(file_model, code=201)
    def post(self):
        """Upload a new file"""
        args = upload_parser.parse_args()
        uploaded_file = args['file']
        name = args['name']

        if not uploaded_file or uploaded_file.filename == '':
            ns.abort(400, 'No file selected')


        file_id = str(uuid.uuid4())
        filename = secure_filename(uploaded_file.filename)
        local_path = get_local_file_path(f'{file_id}-{filename}')

        uploaded_file.save(local_path)

        new_file = {
            'id': file_id,
            'name': name,
            'createdAt': datetime.utcnow().isoformat() + 'Z',
            'status': 0,
            'url': local_path
        }

        files = load_files()
        files.append(new_file)
        save_files(files)

        return new_file, 201


@ns.route('/<string:file_id>')
class FileResource(Resource):
    @ns.marshal_with(file_model)
    def get(self, file_id):
        """Get a specific file"""
        files = load_files()
        file = next((f for f in files if f['id'] == file_id), None)
        if file is None:
            ns.abort(404, 'File not found')
        return file

    @ns.expect(file_model)
    @ns.marshal_with(file_model)
    def put(self, file_id):
        """Update file metadata"""
        files = load_files()
        file_index = next((i for i, f in enumerate(files) if f['id'] == file_id), None)
        if file_index is None:
            ns.abort(404, 'File not found')

        data = request.json
        files[file_index]['name'] = data.get('name', files[file_index]['name'])
        files[file_index]['status'] = data.get('status', files[file_index]['status'])
        save_files(files)

        return files[file_index]

    @ns.response(204, 'File deleted')
    def delete(self, file_id):
        """Delete a file"""
        files = load_files()
        file = next((f for f in files if f['id'] == file_id), None)
        if file is None:
            ns.abort(404, 'File not found')

        # Delete from file system
        try:
            if os.path.exists(file['url']):
                os.remove(file['url'])
        except Exception as e:
            app.logger.error(f"Failed to delete file from disk: {str(e)}")

        # Delete from JSON
        files = [f for f in files if f['id'] != file_id]
        save_files(files)
        return '', 204

@ns.route('/speaker-identification/<string:file_id>')
class SpeakerIdentification(Resource):
    def put(self, file_id):
        """Update file metadata"""
        files = load_files()
        file_index = next((i for i, f in enumerate(files) if f['id'] == file_id), None)
        if file_index is None:
            ns.abort(404, 'File not found')

        # No longer checking for request.json
        files[file_index]['status'] = 1
        thread = threading.Thread(target=speaker_identification_service, args=(file_id,HF_TOKEN,))
        thread.start()
        save_files(files)
        return files[file_index]

@ns.route('/speaker-diarization/<string:file_id>')
class SpeakerDiarization(Resource):
    def put(self, file_id):
        """Update file metadata"""
        files = load_files()
        file_index = next((i for i, f in enumerate(files) if f['id'] == file_id), None)
        if file_index is None:
            ns.abort(404, 'File not found')

        # No longer checking for request.json
        files[file_index]['status'] = 3
        save_files(files)
        thread = threading.Thread(target=speaker_diarization_service, args=(file_id,))
        thread.start()
     

        return files[file_index]

@ns.route('/speech-recognition/<string:file_id>')
class SpeechRecognition(Resource):
    def put(self, file_id):
        """Update file metadata"""
        files = load_files()
        file_index = next((i for i, f in enumerate(files) if f['id'] == file_id), None)
        if file_index is None:
            ns.abort(404, 'File not found')

        files[file_index]['status'] = 5
        save_files(files)
        thread = threading.Thread(target=speech_recognition_service, args=(file_id,))
        thread.start()
        return files[file_index]

@ns.route('/language-identification/<string:file_id>')
class LanguageIdentification(Resource):
    def put(self, file_id):
        """Update file metadata"""
        files = load_files()
        file_index = next((i for i, f in enumerate(files) if f['id'] == file_id), None)
        if file_index is None:
            ns.abort(404, 'File not found')

        # No longer checking for request.json
        # files[file_index]['status'] = 7
        files[file_index]['status'] = 8


        save_files(files)

        return files[file_index]


@ns.route('/neural-translation/<string:file_id>')
class NeuralTranslation(Resource):
    def put(self, file_id):
        """Update file metadata"""
        files = load_files()
        file_index = next((i for i, f in enumerate(files) if f['id'] == file_id), None)
        if file_index is None:
            ns.abort(404, 'File not found')

        # No longer checking for request.json
        files[file_index]['status'] = 10
        save_files(files)

        return files[file_index]

        
@app.route('/download/<string:file_id>')
def download_file(file_id):
    """Download file by ID"""
    files = load_files()
    file = next((f for f in files if f['id'] == file_id), None)

    if not file or not os.path.exists(file['url']):
        return jsonify({'message': 'File not found'}), 404

    return send_from_directory(directory=os.path.dirname(file['url']),
                               path=os.path.basename(file['url']),
                               as_attachment=True)

@app.route('/uploads/<path:filename>')
def serve_uploaded_file(filename):
    """Serve any uploaded file directly by filename"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/')
def index():
    return 'Smart Audio System API is running. Visit /swagger.json or /docs if enabled.'


if __name__ == '__main__':
    app.run(debug=True)
