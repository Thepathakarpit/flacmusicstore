from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import os
import json

# Scopes for accessing Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Temporary directory for downloaded files
TEMP_DOWNLOAD_DIR = os.getenv('TEMP_DOWNLOAD_DIR', 'downloads/')

def get_drive_service():
    """Authenticate and return a Google Drive API service."""
    creds = None

    # Check if token.json exists for saved credentials
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If credentials are invalid or not found, initialize OAuth flow
    if not creds or not creds.valid:
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

        if not client_id or not client_secret:
            raise Exception("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in environment variables.")

        # Prepare OAuth client configuration
        client_config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"]
            }
        }

        # Use InstalledAppFlow to generate the token
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        print("Visit the following URL to authorize the application:")
        print(flow.authorization_url(prompt='consent')[0])

        # Prompt user to input the authorization code manually
        auth_code = input("Enter the authorization code: ").strip()
        creds = flow.fetch_token(code=auth_code)

        # Save the credentials for future use
        with open('token.json', 'w') as token_file:
            token_file.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def stream_file(file_id):
    """Stream a file's content directly from Google Drive."""
    service = get_drive_service()
    try:
        # Fetch file metadata
        file_metadata = service.files().get(fileId=file_id, fields='id,name,mimeType').execute()
        print(f"Streaming file: {file_metadata['name']} ({file_metadata['mimeType']})")

        # Get the file content as a stream
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"Streaming progress: {int(status.progress() * 100)}%")

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
        print(f"Downloading file: {file_metadata['name']} ({file_metadata['mimeType']})")

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
                print(f"Download progress: {int(status.progress() * 100)}%")

        print(f"File downloaded successfully: {file_path}")
        return file_path
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        raise Exception(f"Error downloading file: {str(e)}")
