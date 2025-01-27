from flask import Flask, jsonify, request, send_file, Response
from flask_cors import CORS
import pandas as pd
import os
import requests
import io
import mimetypes

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Constants
TEMP_DOWNLOAD_DIR = 'temp_downloads'
BASE_EXPORT_URL = "https://drive.google.com/uc?export=download&id="

def get_confirm_token(response):
    """Extract confirmation token from Google Drive response"""
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None

def get_content_type(filename):
    """Get the content type based on file extension"""
    extension = os.path.splitext(filename)[1].lower()
    if extension == '.flac':
        return 'audio/flac'
    elif extension == '.mp3':
        return 'audio/mpeg'
    elif extension == '.m4a':
        return 'audio/mp4'
    elif extension == '.wav':
        return 'audio/wav'
    return 'application/octet-stream'

def download_and_cache_file(file_id):
    """Download and cache a file from Google Drive with confirmation handling"""
    try:
        session = requests.Session()
        
        # First request to get the confirmation token
        file_url = f"{BASE_EXPORT_URL}{file_id}"
        response = session.get(file_url, stream=True)

        if response.status_code == 404:
            raise Exception("File not found. Ensure the file ID is correct and the file is publicly accessible.")

        # Check if we need to confirm the download
        token = get_confirm_token(response)
        if token:
            params = {'id': file_id, 'confirm': token}
            response = session.get(BASE_EXPORT_URL, params=params, stream=True)

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
                if chunk:  # Filter out keep-alive chunks
                    file.write(chunk)

        return file_path

    except requests.RequestException as e:
        print(f"Error downloading file: {str(e)}")
        raise Exception(f"Error downloading file: {str(e)}")

def search_tracks(query):
    """Search tracks in the CSV file"""
    try:
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tracks.csv')
        df = pd.read_csv(csv_path)
        
        # Convert query and searchable columns to lowercase for case-insensitive search
        query = query.lower()
        
        # Search in relevant columns (adjust these based on your CSV structure)
        mask = df['title'].str.lower().str.contains(query, na=False) | \
               df['artist'].str.lower().str.contains(query, na=False)
        
        results = df[mask].to_dict('records')
        return results
    except Exception as e:
        print(f"Error searching tracks: {str(e)}")
        raise

@app.route('/api/search', methods=['GET'])
def search():
    try:
        query = request.args.get('q', '')
        print(f"Searching for: {query}")
        
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tracks.csv')
        if not os.path.exists(csv_path):
            return jsonify({
                'error': 'Database file not found',
                'path': csv_path
            }), 404
            
        results = search_tracks(query)
        return jsonify(results)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'type': type(e).__name__
        }), 500

@app.route('/api/download/<file_id>', methods=['GET'])
def download(file_id):
    try:
        file_path = download_and_cache_file(file_id)
        content_type = get_content_type(file_path)
        return send_file(file_path, 
                        as_attachment=True,
                        mimetype=content_type)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/stream/<file_id>')
def stream(file_id):
    try:
        session = requests.Session()
        
        # First request to get the confirmation token
        file_url = f"{BASE_EXPORT_URL}{file_id}"
        response = session.get(file_url, stream=True)
        
        # Check if we need to confirm the download
        token = get_confirm_token(response)
        if token:
            params = {'id': file_id, 'confirm': token}
            response = session.get(BASE_EXPORT_URL, params=params, stream=True)

        if response.status_code != 200:
            raise Exception("Failed to fetch file from Google Drive")

        # Get content type from response headers or filename
        content_type = response.headers.get('Content-Type', 'audio/flac')
        if 'content-disposition' in response.headers:
            filename = response.headers['content-disposition'].split('filename=')[-1].strip('"')
            content_type = get_content_type(filename)

        # Get file size for Content-Length header
        content_length = response.headers.get('Content-Length')

        # Handle range requests
        range_header = request.headers.get('Range', None)
        if range_header:
            bytes_range = range_header.replace('bytes=', '').split('-')
            start = int(bytes_range[0])
            end = int(bytes_range[1]) if bytes_range[1] else None
            if end:
                length = end - start + 1
            else:
                length = int(content_length) - start if content_length else None
            
            headers = {
                'Content-Type': content_type,
                'Accept-Ranges': 'bytes',
                'Content-Range': f'bytes {start}-{end or int(content_length)-1}/{content_length}',
                'Content-Length': str(length)
            }
            return Response(
                response.iter_content(chunk_size=8192),
                206,
                headers=headers,
                direct_passthrough=True
            )

        headers = {
            'Content-Type': content_type,
            'Accept-Ranges': 'bytes',
            'Content-Length': content_length,
            'Cache-Control': 'no-cache'
        }

        return Response(
            response.iter_content(chunk_size=8192),
            200,
            headers=headers,
            direct_passthrough=True
        )
    except Exception as e:
        print(f"Streaming error: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({
        'status': 'ok',
        'message': 'API is running'
    })

if __name__ == '__main__':
    app.run(debug=True)
