import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Get folder paths from environment variables (with defaults if not found)
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')

# Example in .env: ALLOWED_EXTENSIONS=mp3,wav,flac
ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'mp3,wav').split(','))

# Get JSON storage folder path
JSON_STORAGE = os.getenv('JSON_STORAGE', 'storage/json')

# Ensure all required directories exist
folders_to_create = [
    UPLOAD_FOLDER,
]

for folder in folders_to_create:
    os.makedirs(folder, exist_ok=True)  # Creates folder if it doesn't exist
