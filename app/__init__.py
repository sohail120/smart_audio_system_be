from flask import Flask
from .config import Config
from .extensions import api

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    api.init_app(app)
    
    # Import and register namespaces
    from app.resources import items ,upload_file

    
    api.add_namespace(items.items_ns)
    api.add_namespace(upload_file.upload_file_ns)

    
    return app