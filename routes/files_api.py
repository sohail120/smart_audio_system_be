import uuid
from datetime import datetime
from flask_restx import Namespace, Resource
from werkzeug.datastructures import FileStorage
from utils import load_files, save_files
from models.swagger_models import register_models
from flask import jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
import threading
from services.speaker_diarization_service import speaker_diarization_service
from services.speaker_identification_service import speaker_identification_service
from services.speech_recognition_service import speech_recognition_service
from services.neural_translation_service import neural_translation_service

ns = Namespace('files', description='File operations')

file_model = None  # Will be set in init_api

upload_parser = ns.parser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True, help='The file to upload')
file_model = register_models(ns)


@ns.route('/upload-file')
class FileUpload(Resource):
    @ns.expect(upload_parser)
    @ns.marshal_with(file_model, code=201)
    @ns.response(400, 'Bad request')
    def post(self):
        args = upload_parser.parse_args()
        uploaded_file = args['file']
        file_id = str(uuid.uuid4())

        AUDIO_FILE = os.getenv('AUDIO_FILE', 'audio-file')
        folder_path = os.path.join('uploads', file_id)
        os.makedirs(folder_path, exist_ok=True)

        # Extract original file extension (lowercase)
        _, ext = os.path.splitext(uploaded_file.filename)
        ext = ext.lower()

        # Create final file name with extension
        final_filename = f"{AUDIO_FILE}{ext}"

        # Get the local path to save the file
        local_path=os.path.join(folder_path,secure_filename(final_filename))
        
        uploaded_file.save(local_path)

        # Store file info (including name with extension)
        new_file = {
            'id': file_id,
            'filename': final_filename,  # store uuid + extension
            'status': 1,
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
        files = load_files()
        file = next((f for f in files if f['id'] == file_id), None)
        if file is None:
            ns.abort(404, 'File not found')
        return file


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


@ns.route('/speaker-identification/<string:file_id>')
class SpeakerIdentification(Resource):
    def put(self, file_id):
        """Update file metadata"""
        files = load_files()
        file_index = next((i for i, f in enumerate(files) if f['id'] == file_id), None)
        if file_index is None:
            ns.abort(404, 'File not found')

        # No longer checking for request.json
        files[file_index]['status'] = 3
        save_files(files)
        thread = threading.Thread(target=speaker_identification_service, args=(file_id,))
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
        thread = threading.Thread(target=neural_translation_service, args=(file_id,))
        thread.start()
        return files[file_index]
# @ns.route('/download/<string:file_id>')
# class FileDownload(Resource):
#     def get(self, file_id):
#         files = load_files()
#         file = next((f for f in files if f['id'] == file_id), None)

#         if not file or not os.path.exists(file['url']):
#             return jsonify({'message': 'File not found'}), 404

#         return send_from_directory(
#             directory=os.path.dirname(file['url']),
#             path=os.path.basename(file['url']),
#             as_attachment=True
#         )
