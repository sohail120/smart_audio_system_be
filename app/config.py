import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://avnadmin:AVNS_FHUgrZ3ROtkh6qzEOUu@pg-137370d3-sohail-a134.j.aivencloud.com:14415/defaultdb?sslmode=require'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
