from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import os
import json
from config import TEMP_DOWNLOAD_DIR

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        # Get credentials from environment variable
        creds_json = os.environ.get('GOOGLE_DRIVE_CREDENTIALS')
        if not creds_json:
            raise Exception("Google Drive credentials not found in environment variables")
        
        # Parse the credentials JSON
        try:
            client_config = json.loads(creds_json)
            
            # Ensure the client config has the expected format
            if 'web' not in client_config:
                raise Exception("Invalid client config format")
                
            # Create the flow with the correct client config format
            flow = Flow.from_client_config(
                client_config=client_config,
                scopes=SCOPES
            )
            
            # Set the redirect URI to match your GitHub Pages URL
            flow.redirect_uri = "https://thepathakarpit.github.io/flacmusicstore/"
            
            # Run the local server flow
            creds = flow.run_local_server(port=0)
            
            # Save the credentials for future use
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
                
        except json.JSONDecodeError:
            raise Exception("Invalid JSON format in GOOGLE_DRIVE_CREDENTIALS")
            
    return build('drive', 'v3', credentials=creds)

def stream_file(file_id):
    service = get_drive_service()
    try:
        # Get file metadata first
        file_metadata = service.files().get(fileId=file_id, fields='id,name,mimeType').execute()
        
        # Get the file content
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"Download {int(status.progress() * 100)}%")
        
        # Reset buffer position
        fh.seek(0)
        
        # Return the file data
        return fh.read()
    except Exception as e:
        print(f"Error streaming file: {str(e)}")
        raise Exception(f"Error streaming file: {str(e)}")

def download_file(file_id):
    service = get_drive_service()
    
    try:
        # First check if the file exists and is downloadable
        file_metadata = service.files().get(fileId=file_id, fields='id,name,mimeType').execute()
        print(f"File metadata: {file_metadata}")  # Debug print
        
        if 'application/vnd.google-apps.folder' in file_metadata.get('mimeType', ''):
            raise Exception("Cannot download a folder. Please provide a file ID.")
        
        request = service.files().get_media(fileId=file_id)
        
        file_path = os.path.join(TEMP_DOWNLOAD_DIR, file_metadata['name'])
        if not os.path.exists(TEMP_DOWNLOAD_DIR):
            os.makedirs(TEMP_DOWNLOAD_DIR)
            
        fh = io.FileIO(file_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%")
            
        return file_path
    except Exception as e:
        print(f"Error downloading file: {str(e)}")  # Debug print
        raise Exception(f"Error downloading file: {str(e)}")
