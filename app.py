import os
import uuid
from datetime import datetime
from flask import Flask,  jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename
from flask_cors import CORS
from flask_restx import Api, Resource, fields
from werkzeug.datastructures import FileStorage
from utils import load_files, save_files

from services.speech_recognition_service import speech_recognition_service
from services.speaker_identification_service import speaker_identification_service
from services.speaker_diarization_service import speaker_diarization_service

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'pdf', 'docx', 'jpg', 'png'}
JSON_STORAGE = 'files.json'

# Initialize Flask app
app = Flask(__name__)
CORS(app)
# Regular Flask routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/result-page/<string:file_id>')
def result(file_id):
    return render_template('result.html',file_id=file_id)

# Configure Swagger
api = Api(app, 
          version='1.0', 
          title='File Upload API',
          description='A simple API for file upload and management',
          doc='/swagger')

# Namespace for file operations
ns = api.namespace('files', description='File operations')

# Swagger models
file_model = ns.model('File', {
    'id': fields.String(readonly=True, description='The file identifier'),
    'name': fields.String(required=True, description='The file name'),
    'createdAt': fields.String(readonly=True, description='Creation timestamp'),
    'status': fields.Integer(description='File processing status'),
    'url': fields.String(description='Local file path')
})

upload_parser = ns.parser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True, help='The file to upload')
upload_parser.add_argument('name', location='form', required=True, help='Display name for the file')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create required directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_local_file_path(filename):
    return os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))





# API routes with Swagger documentation
@ns.route('/upload-file')
class FileUpload(Resource):
    @ns.expect(upload_parser)
    @ns.marshal_with(file_model, code=201)
    @ns.response(400, 'Bad request')
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
            'status': 1,
            'url': local_path
        }

        files = load_files()
        files.append(new_file)
        save_files(files)

        return new_file, 201

@ns.route('/<string:file_id>')
class FileResource(Resource):
    @ns.marshal_with(file_model)
    @ns.response(404, 'File not found')
    def get(self, file_id):
        """Get a specific file"""
        files = load_files()
        file = next((f for f in files if f['id'] == file_id), None)
        if file is None:
            ns.abort(404, 'File not found')
        return file


@app.route('/download/<string:file_id>')
def download_file(file_id):
    """Download file by ID"""
    files = load_files()
    file = next((f for f in files if f['id'] == file_id), None)

    if not file or not os.path.exists(file['url']):
        return jsonify({'message': 'File not found'}), 404

    return send_from_directory(
        directory=os.path.dirname(file['url']),
        path=os.path.basename(file['url']),
        as_attachment=True
    )

if __name__ == '__main__':
    app.run(debug=True)