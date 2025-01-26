import os
import json

# Google Drive API Configuration
GOOGLE_DRIVE_CREDENTIALS = json.loads(os.environ.get('GOOGLE_DRIVE_CREDENTIALS', '{}'))
DRIVE_FOLDER_ID = os.environ.get('DRIVE_FOLDER_ID', '1O5AnabJwMK7z7TmIhW-PUZnrn4Jzx4de')

# CSV Configuration
TRACKS_CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'tracks.csv')

# Temporary download directory
TEMP_DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), 'temp_downloads') 
