from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import requests
import io
import os
import json
from config import TEMP_DOWNLOAD_DIR

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")

# Base URL for Google Drive file download
BASE_EXPORT_URL = "https://drive.google.com/uc?export=download&id="

def get_drive_service(file_id):
    try:
        # Construct the file download URL
        file_url = f"{BASE_EXPORT_URL}{file_id}"

        # Send a GET request to download the file
        response = requests.get(file_url, stream=True, allow_redirects=True)

        if response.status_code == 404:
            raise Exception("File not found. Ensure the file ID is correct and the file is publicly accessible.")

        # Use file ID as fallback file name
        file_name = f"{file_id}.file"

        # Extract filename from headers if available
        if 'content-disposition' in response.headers:
            content_disposition = response.headers['content-disposition']
            if 'filename=' in content_disposition:
                file_name = content_disposition.split('filename=')[-1].strip('"')

        # Ensure the download directory exists
        if not os.path.exists(TEMP_DOWNLOAD_DIR):
            os.makedirs(TEMP_DOWNLOAD_DIR)

        file_path = os.path.join(TEMP_DOWNLOAD_DIR, file_name)

        # Write the file content to disk
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        print(f"File downloaded successfully: {file_path}")
        return file_path

    except requests.RequestException as e:
        print(f"Error downloading file: {str(e)}")
        raise Exception(f"Error downloading file: {str(e)}")

def stream_file(file_id):
    service = get_drive_service(file_id)
    try:
        # Get file metadata first
        file_metadata = service.files().get(fileId=file_id, fields='id,name,mimeType').execute()
        print(f"Streaming file metadata: {file_metadata}")

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
    service = get_drive_service(file_id)

    try:
        # First check if the file exists and is downloadable
        file_metadata = service.files().get(fileId=file_id, fields='id,name,mimeType').execute()
        print(f"File metadata: {file_metadata}")

        if file_metadata.get('mimeType') == 'application/vnd.google-apps.folder':
            raise Exception("Cannot download a folder. Please provide a file ID.")

        request = service.files().get_media(fileId=file_id)

        file_path = os.path.join(TEMP_DOWNLOAD_DIR, file_metadata['name'])
        if not os.path.exists(TEMP_DOWNLOAD_DIR):
            os.makedirs(TEMP_DOWNLOAD_DIR)

        with open(file_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print(f"Download {int(status.progress() * 100)}%")

        return file_path
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        raise Exception(f"Error downloading file: {str(e)}")
