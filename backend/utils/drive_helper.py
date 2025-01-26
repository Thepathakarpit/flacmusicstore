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
    try:
        # Get credentials from environment variable
        creds_json = os.environ.get('GOOGLE_DRIVE_CREDENTIALS')
        if not creds_json:
            raise Exception("Google Drive credentials not found in environment variables")
            
        # Parse the JSON string into a dictionary
        client_config = json.loads(creds_json)
        
        # Create OAuth2 flow
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri="https://thepathakarpit.github.io/flacmusicstore/"
        )
        
        # Get the authorization URL
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        # Get the refresh token from environment variable
        refresh_token = os.environ.get('GOOGLE_DRIVE_REFRESH_TOKEN')
        if not refresh_token:
            print("Please visit this URL to authorize the application:", auth_url)
            raise Exception("Refresh token not found. Please authenticate first.")
        
        # Create credentials using client config and refresh token
        creds = Credentials(
            None,  # No access token needed initially
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_config['web']['client_id'],
            client_secret=client_config['web']['client_secret'],
            scopes=SCOPES
        )
        
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"Error creating drive service: {str(e)}")
        raise Exception(f"Failed to initialize Google Drive service: {str(e)}")

def stream_file(file_id):
    print("\n=== Starting file stream process ===")
    try:
        print("Getting drive service...")
        service = get_drive_service()
        print("Drive service obtained successfully")
        
        print(f"Requesting metadata for file: {file_id}")
        # Get file metadata first
        file_metadata = service.files().get(fileId=file_id, fields='id,name,mimeType').execute()
        print(f"File metadata retrieved successfully: {file_metadata}")
        
        print("Initiating media download request...")
        # Get the file content
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        print("Download request initialized")
        
        print("Starting chunk download...")
        done = False
        chunk_count = 0
        while not done:
            chunk_count += 1
            print(f"Downloading chunk {chunk_count}...")
            status, done = downloader.next_chunk()
            if status:
                print(f"Download progress: {int(status.progress() * 100)}%")
        
        print("Download completed, resetting buffer position")
        # Reset buffer position
        fh.seek(0)
        
        # Get the size of downloaded data
        data = fh.read()
        print(f"File size: {len(data)} bytes")
        
        if len(data) == 0:
            raise Exception("Downloaded file is empty")
            
        print("=== File stream process completed successfully ===\n")
        return data
        
    except Exception as e:
        print("\n=== Error in stream_file ===")
        print(f"Error type: {type(e)}")
        print(f"Error message: {str(e)}")
        print(f"Error location: {e.__traceback__.tb_frame.f_code.co_name}")
        print("=== End of error details ===\n")
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
