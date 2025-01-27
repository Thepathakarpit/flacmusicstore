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
        creds_json = os.environ.get('GOOGLE_DRIVE_CREDENTIALS')
        if not creds_json:
            raise Exception("Google Drive credentials not found in environment variables")

        try:
            client_secret_data = json.loads(creds_json)
            
            # Use web configuration matching your GitHub Pages setup
            client_config = {
                "web": {
                    "client_id": client_secret_data["web"]["client_id"],
                    "client_secret": client_secret_data["web"]["client_secret"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": client_secret_data["web"]["redirect_uris"]
                }
            }

            flow = Flow.from_client_config(
                client_config=client_config,
                scopes=SCOPES,
                redirect_uri=client_secret_data["web"]["redirect_uris"][0]
            )

            # Generate authorization URL for manual initialization
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                prompt='consent'
            )
            
            print(f"MANUAL STEP REQUIRED: Visit this URL to authorize:\n{auth_url}")
            print("Then paste the authorization code below:")
            code = input("Enter authorization code: ")
            
            flow.fetch_token(code=code)
            creds = flow.credentials
            
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        except json.JSONDecodeError:
            raise Exception("Invalid JSON format in GOOGLE_DRIVE_CREDENTIALS")
        except KeyError as e:
            raise Exception(f"Missing required field in credentials: {str(e)}")
            
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
