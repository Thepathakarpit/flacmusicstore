
from flask import Flask, jsonify, request, send_file, Response
from flask_cors import CORS
import pandas as pd
import os
import requests
import io
import mimetypes

app = Flask(__name__)

# Enhanced CORS configuration for better cross-origin support
CORS(app, 
     resources={
         r"/api/*": {
             "origins": ["*"],  # Allow all origins
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Allow all methods
             "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
             "supports_credentials": True
         },
         r"/stream/*": {
             "origins": ["*"],
             "methods": ["GET", "HEAD", "OPTIONS"],
             "allow_headers": ["Range", "Content-Type"],
             "expose_headers": ["Content-Range", "Accept-Ranges", "Content-Length"]
         }
     },
     origins="*",  # Global fallback
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Range"],
     expose_headers=["Content-Range", "Accept-Ranges", "Content-Length"],
     supports_credentials=True
)

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

@app.route('/api/search', methods=['GET', 'OPTIONS'])
def search():
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        return response
    
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
        response = jsonify(results)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({
            'error': str(e),
            'type': type(e).__name__
        }), 500
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

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
        file_url = f"{BASE_EXPORT_URL}{file_id}"
        
        # Initial request to handle Google Drive's download page
        response = session.get(file_url, stream=True)
        if response.status_code != 200:
            return jsonify({'error': 'Failed to access file'}), 404

        # Handle Google Drive confirmation token
        token = get_confirm_token(response)
        if token:
            params = {'id': file_id, 'confirm': token}
            response = session.get(BASE_EXPORT_URL, params=params, stream=True)
            if response.status_code != 200:
                return jsonify({'error': 'Failed to confirm download'}), 400

        # Determine content type and size
        content_type = response.headers.get('Content-Type', 'audio/flac')
        if 'content-disposition' in response.headers:
            filename = response.headers['content-disposition'].split('filename=')[-1].strip('"')
            content_type = get_content_type(filename)

        content_length = response.headers.get('Content-Length')
        if not content_length:
            # If content length is not provided, we need to get it
            response = session.get(file_url, stream=True, headers={'Range': 'bytes=0-1'})
            content_length = response.headers.get('Content-Range', '').split('/')[-1]
            if not content_length or content_length == '*':
                return jsonify({'error': 'Could not determine file size'}), 400
            # Reset the response for actual streaming
            response = session.get(file_url, stream=True)

        content_length = int(content_length)
        
        # Handle range requests (for seeking in audio player)
        range_header = request.headers.get('Range')
        if range_header:
            try:
                bytes_range = range_header.replace('bytes=', '').split('-')
                start = int(bytes_range[0])
                end = int(bytes_range[1]) if bytes_range[1] else content_length - 1
                
                if start >= content_length:
                    return Response(status=416)  # Range Not Satisfiable
                
                # Adjust end if it exceeds content_length
                end = min(end, content_length - 1)
                length = end - start + 1

                # Make a new request with the range
                headers = {'Range': f'bytes={start}-{end}'}
                response = session.get(file_url, headers=headers, stream=True)
                
                if response.status_code == 206:  # Partial Content
                    headers = {
                        'Content-Type': content_type,
                        'Accept-Ranges': 'bytes',
                        'Content-Range': f'bytes {start}-{end}/{content_length}',
                        'Content-Length': str(length),
                        'Cache-Control': 'no-cache'
                    }
                    return Response(
                        response.iter_content(chunk_size=8192),
                        206,
                        headers=headers,
                        direct_passthrough=True
                    )
            except (ValueError, IndexError) as e:
                print(f"Range parsing error: {str(e)}")
                # If range parsing fails, fall back to full file
                response = session.get(file_url, stream=True)

        # Return full file if no range request or range parsing failed
        headers = {
            'Content-Type': content_type,
            'Accept-Ranges': 'bytes',
            'Content-Length': str(content_length),
            'Cache-Control': 'no-cache'
        }

        return Response(
            response.iter_content(chunk_size=8192),
            200,
            headers=headers,
            direct_passthrough=True
        )

    except requests.RequestException as e:
        print(f"Streaming error (RequestException): {str(e)}")
        return jsonify({'error': 'Failed to stream file'}), 500
    except Exception as e:
        print(f"Streaming error (General): {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/test', methods=['GET', 'OPTIONS'])
def test():
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        return response
    
    response = jsonify({
        'status': 'ok',
        'message': 'API is running',
        'cors': 'enabled',
        'timestamp': pd.Timestamp.now().isoformat()
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

if __name__ == '__main__':
    app.run(debug=True)
