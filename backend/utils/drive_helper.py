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
        print("\n=== Initializing Drive Service ===")
        # Get credentials from environment variable
        creds_json = os.environ.get('GOOGLE_DRIVE_CREDENTIALS')
        if not creds_json:
            raise Exception("Google Drive credentials not found in environment variables")
            
        # Parse the JSON string into a dictionary
        try:
            client_config = json.loads(creds_json)
            print("Successfully parsed credentials JSON")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse credentials JSON: {str(e)}")
        
        # Get the refresh token from environment variable
        refresh_token = os.environ.get('GOOGLE_DRIVE_REFRESH_TOKEN')
        if not refresh_token:
            print("Refresh token not found in environment variables")
            raise Exception("Refresh token not found. Please authenticate first.")
        
        print("Creating credentials object...")
        # Create credentials using client config and refresh token
        creds = Credentials(
            None,  # No access token needed initially
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_config['web']['client_id'],
            client_secret=client_config['web']['client_secret'],
            scopes=SCOPES
        )
        
        print("Building drive service...")
        service = build('drive', 'v3', credentials=creds)
        print("=== Drive Service initialized successfully ===\n")
        return service
        
    except Exception as e:
        print("\n=== Error in get_drive_service ===")
        print(f"Error type: {type(e)}")
        print(f"Error message: {str(e)}")
        print("=== End of error details ===\n")
        raise Exception(f"Failed to initialize Google Drive service: {str(e)}")

def stream_file(file_id):
    print(f"\n=== Starting stream_file for ID: {file_id} ===")
    try:
        print("Getting drive service...")
        service = get_drive_service()
        
        print("Requesting file metadata...")
        try:
            file_metadata = service.files().get(
                fileId=file_id, 
                fields='id,name,mimeType,size'
            ).execute()
            print(f"File metadata retrieved: {file_metadata}")
        except Exception as e:
            raise Exception(f"Failed to get file metadata: {str(e)}")
        
        print("Initiating media download request...")
        try:
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
        except Exception as e:
            raise Exception(f"Failed to initialize download request: {str(e)}")
        
        print("Starting chunk download...")
        done = False
        chunk_count = 0
        while not done:
            try:
                chunk_count += 1
                print(f"Downloading chunk {chunk_count}...")
                status, done = downloader.next_chunk()
                if status:
                    print(f"Download progress: {int(status.progress() * 100)}%")
            except Exception as e:
                raise Exception(f"Error downloading chunk {chunk_count}: {str(e)}")
        
        print("Download completed, preparing data...")
        fh.seek(0)
        data = fh.read()
        
        if not data:
            raise Exception("Downloaded file is empty")
        
        print(f"Successfully downloaded {len(data)} bytes")
        print("=== stream_file completed successfully ===\n")
        return data
        
    except Exception as e:
        print("\n=== Error in stream_file ===")
        print(f"Error type: {type(e)}")
        print(f"Error message: {str(e)}")
        print(f"File ID: {file_id}")
        print("=== End of error details ===\n")
        raise Exception(f"Error streaming file: {str(e)}")

def download_file(file_id):
    print(f"\n=== Starting download_file for ID: {file_id} ===")
    try:
        service = get_drive_service()
        
        print("Checking file metadata...")
        try:
            file_metadata = service.files().get(
                fileId=file_id, 
                fields='id,name,mimeType,size'
            ).execute()
            print(f"File metadata: {file_metadata}")
        except Exception as e:
            raise Exception(f"Failed to get file metadata: {str(e)}")
        
        if 'application/vnd.google-apps.folder' in file_metadata.get('mimeType', ''):
            raise Exception("Cannot download a folder. Please provide a file ID.")
        
        print("Creating download directory if needed...")
        if not os.path.exists(TEMP_DOWNLOAD_DIR):
            os.makedirs(TEMP_DOWNLOAD_DIR)
            
        file_path = os.path.join(TEMP_DOWNLOAD_DIR, file_metadata['name'])
        print(f"Download path: {file_path}")
        
        print("Initiating download...")
        request = service.files().get_media(fileId=file_id)
        with io.FileIO(file_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}%")
        
        print(f"File downloaded successfully to: {file_path}")
        print("=== download_file completed successfully ===\n")
        return file_path
        
    except Exception as e:
        print("\n=== Error in download_file ===")
        print(f"Error type: {type(e)}")
        print(f"Error message: {str(e)}")
        print(f"File ID: {file_id}")
        print("=== End of error details ===\n")
        raise Exception(f"Error downloading file: {str(e)}") 
