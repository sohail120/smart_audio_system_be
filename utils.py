import os
import json  # Ad

JSON_STORAGE = 'files.json'

# Helper Functions
def load_files(JSON_STORAGE=JSON_STORAGE):
    if not os.path.exists(JSON_STORAGE):
        return []
    try:
        with open(JSON_STORAGE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_files(files,JSON_STORAGE=JSON_STORAGE):
    with open(JSON_STORAGE, 'w') as f:
        json.dump(files, f, indent=2)