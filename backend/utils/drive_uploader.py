from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import sys
import pandas as pd

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GOOGLE_DRIVE_CREDENTIALS, TRACKS_CSV_PATH

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_drive_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            GOOGLE_DRIVE_CREDENTIALS, 
            SCOPES,
            redirect_uri='http://localhost:8080/oauth2callback'
        )
        creds = flow.run_local_server(
            port=8080,
            prompt='consent',
            access_type='offline'
        )
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def create_music_folder():
    service = get_drive_service()
    
    # Create 'FLAC Music Store' folder
    folder_metadata = {
        'name': 'FLAC Music Store',
        'mimeType': 'application/vnd.google-apps.folder'
    }
    
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    
    # Make folder publicly accessible for viewing
    permission = {
        'type': 'anyone',
        'role': 'reader'
    }
    service.permissions().create(fileId=folder['id'], body=permission).execute()
    
    return folder['id']

def upload_music_file(file_path, folder_id):
    service = get_drive_service()
    
    file_name = os.path.basename(file_path)
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    
    media = MediaFileUpload(
        file_path,
        mimetype='audio/flac',
        resumable=True
    )
    
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    
    # Make file publicly accessible for viewing
    permission = {
        'type': 'anyone',
        'role': 'reader'
    }
    service.permissions().create(fileId=file['id'], body=permission).execute()
    
    return {
        'title': os.path.splitext(file_name)[0],
        'file_id': file['id']
    }

def update_csv(tracks_data):
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(TRACKS_CSV_PATH), exist_ok=True)
    
    if not os.path.exists(TRACKS_CSV_PATH):
        df = pd.DataFrame(columns=['title', 'artist', 'album', 'file_id'])
        df.to_csv(TRACKS_CSV_PATH, index=False)
    
    df = pd.read_csv(TRACKS_CSV_PATH)
    new_df = pd.DataFrame(tracks_data)
    df = pd.concat([df, new_df], ignore_index=True)
    df.to_csv(TRACKS_CSV_PATH, index=False)

if __name__ == '__main__':
    # Create the music folder
    folder_id = "1kRhz_VMqYj9fn9LwuqWo-uBbAIxYeypW"
    # folder_id = create_music_folder()
    # print(f"Created folder with ID: {folder_id}")
    
    # Update this path to your FLAC files directory
    music_dir = input("Enter the path to your FLAC files directory: ")
    
    uploaded_tracks = []
    for file in os.listdir(music_dir):
        if file.endswith('.flac'):
            print(f"Uploading {file}...")
            file_path = os.path.join(music_dir, file)
            track_info = upload_music_file(file_path, folder_id)
            
            # You can modify this to extract more metadata if needed
            track_info['artist'] = file
            track_info['album'] = file
            
            uploaded_tracks.append(track_info)
    
    # Update the CSV file with new tracks
    update_csv(uploaded_tracks)
    print("Upload complete! CSV file has been updated.")
    
    # Print instructions for updating config.py
    print("\nIMPORTANT: Update your config.py with the following folder ID:")
    print(f"DRIVE_FOLDER_ID = '{folder_id}'") 