from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import os
import json

# Temporary directory for downloads
TEMP_DOWNLOAD_DIR = "downloads/"

# Scopes for accessing Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    """Authenticate and return a Google Drive API service."""
    creds = None

    # Check for existing credentials
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If credentials are invalid or not found, start the OAuth flow
    if not creds or not creds.valid:
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

        if not client_id or not client_secret:
            raise Exception("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET not found in environment variables")

        # Prepare client configuration for OAuth
        client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [
                    "http://localhost:8080/oauth2callback",
                    "https://thepathakarpit.github.io/flacmusicstore/frontend"
                ]
            }
        }

        # Start the OAuth flow
        flow = Flow.from_client_config(client_config, scopes=SCOPES)
        flow.redirect_uri = "http://localhost:8080/oauth2callback" if os.getenv('LOCAL_DEV') else "https://thepathakarpit.github.io/flacmusicstore/frontend"

        creds = flow.run_local_server(port=8080)

        # Save the credentials for future use
        with open('token.json', 'w') as token_file:
            token_file.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def stream_file(file_id):
    """Stream a file's content from Google Drive."""
    service = get_drive_service()
    try:
        # Fetch file metadata
        file_metadata = service.files().get(fileId=file_id, fields='id,name,mimeType').execute()
        
        # Download file content as stream
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"Download {int(status.progress() * 100)}%")
        
        fh.seek(0)  # Reset the buffer position
        return fh.read()
    except Exception as e:
        print(f"Error streaming file: {str(e)}")
        raise Exception(f"Error streaming file: {str(e)}")

def download_file(file_id):
    """Download a file from Google Drive."""
    service = get_drive_service()
    try:
        # Fetch file metadata
        file_metadata = service.files().get(fileId=file_id, fields='id,name,mimeType').execute()
        print(f"File metadata: {file_metadata}")

        # Ensure it's not a folder
        if 'application/vnd.google-apps.folder' in file_metadata.get('mimeType', ''):
            raise Exception("Cannot download a folder. Please provide a valid file ID.")

        # Prepare the download path
        file_path = os.path.join(TEMP_DOWNLOAD_DIR, file_metadata['name'])
        if not os.path.exists(TEMP_DOWNLOAD_DIR):
            os.makedirs(TEMP_DOWNLOAD_DIR)

        # Download the file
        request = service.files().get_media(fileId=file_id)
        with open(file_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}% completed")

        print(f"File downloaded successfully: {file_path}")
        return file_path
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        raise Exception(f"Error downloading file: {str(e)}")
