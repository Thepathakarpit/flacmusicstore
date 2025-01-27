from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import os
import json
from config import TEMP_DOWNLOAD_DIR

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


def get_credentials():
    """Get valid credentials from environment variable"""
    try:
        # Get credentials from environment variable
        creds_json = os.getenv('GOOGLE_DRIVE_CREDENTIALS')
        if not creds_json:
            raise Exception("GOOGLE_DRIVE_CREDENTIALS environment variable not set")
            
        creds_data = json.loads(creds_json)
        creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                
        return creds
    except Exception as e:
        print(f"Error getting credentials: {str(e)}")
        raise

def get_drive_service():
    """Get Google Drive service"""
    try:
        creds = get_credentials()
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Error building drive service: {str(e)}")
        raise
        
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
