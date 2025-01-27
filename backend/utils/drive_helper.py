from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
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
    """Stream a file from Google Drive"""
    try:
        service = get_drive_service()
        
        # Get the file metadata
        file_metadata = service.files().get(fileId=file_id).execute()
        
        # Stream the file
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        
        while done is False:
            status, done = downloader.next_chunk()
            
        fh.seek(0)
        return fh
        
    except Exception as e:
        print(f"Error streaming file: {str(e)}")
        raise

def download_file(file_id):
    """Download a file from Google Drive"""
    try:
        service = get_drive_service()
        
        # Create temp directory if it doesn't exist
        os.makedirs(TEMP_DOWNLOAD_DIR, exist_ok=True)
        
        # Get the file metadata
        file_metadata = service.files().get(fileId=file_id).execute()
        
        # Download the file
        request = service.files().get_media(fileId=file_id)
        file_path = os.path.join(TEMP_DOWNLOAD_DIR, f"{file_id}.flac")
        
        fh = io.FileIO(file_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        
        while done is False:
            status, done = downloader.next_chunk()
            
        return file_path
        
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        raise Exception(f"Error downloading file: {str(e)}" 
