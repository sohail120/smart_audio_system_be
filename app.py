from flask import Flask
from flask_cors import CORS
from flask_restx import Api
from routes.files_api import ns as files_ns
from routes.ui_routes import ui_bp

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB (adjust as needed)
app.config['UPLOAD_FOLDER'] = 'uploads'

CORS(app)

# Register UI routes
app.register_blueprint(ui_bp)


# Swagger API
api = Api(app, version='1.0', title='File Upload API', description='A simple API for file upload and management', doc='/swagger')
api.add_namespace(files_ns)

if __name__ == '__main__':
    app.run(debug=True)
