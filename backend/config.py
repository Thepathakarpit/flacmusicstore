import os
import json

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
TEMP_DIR = os.path.join(BASE_DIR, 'temp_downloads')

# File paths
TRACKS_CSV_PATH = os.path.join(DATA_DIR, 'tracks.csv')

# Google Drive configuration
GOOGLE_DRIVE_CREDENTIALS = json.loads(os.environ.get('GOOGLE_DRIVE_CREDENTIALS', '{}'))
DRIVE_FOLDER_ID = os.environ.get('DRIVE_FOLDER_ID', '1O5AnabJwMK7z7TmIhW-PUZnrn4Jzx4de')

def ensure_data_directories():
    """Ensure all required directories exist"""
    directories = [DATA_DIR, TEMP_DIR]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"[Setup] Ensured directory exists: {directory}")
    
    # Create empty tracks.csv if it doesn't exist
    if not os.path.exists(TRACKS_CSV_PATH):
        import pandas as pd
        df = pd.DataFrame(columns=['title', 'artist', 'album', 'file_id'])
        df.to_csv(TRACKS_CSV_PATH, index=False)
        print(f"[Setup] Created empty tracks.csv at {TRACKS_CSV_PATH}") 
