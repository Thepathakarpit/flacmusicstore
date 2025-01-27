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

# Utility Functions
def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None

def get_content_type(filename):
    extension = os.path.splitext(filename)[1].lower()
    mime = mimetypes.guess_type(filename)[0]
    return mime or 'application/octet-stream'

def download_file(file_id):
    session = requests.Session()
    file_url = f"{BASE_EXPORT_URL}{file_id}"
    response = session.get(file_url, stream=True)

    if response.status_code == 404:
        raise FileNotFoundError("File not found or inaccessible.")

    token = get_confirm_token(response)
    if token:
        response = session.get(file_url, params={'confirm': token}, stream=True)

    file_name = f"{file_id}.file"
    if 'content-disposition' in response.headers:
        content_disposition = response.headers['content-disposition']
        if 'filename=' in content_disposition:
            file_name = content_disposition.split('filename=')[-1].strip('"')

    os.makedirs(TEMP_DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(TEMP_DOWNLOAD_DIR, file_name)

    with open(file_path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)

    return file_path

def search_tracks_in_csv(query):
    csv_path = os.path.join(os.path.dirname(__file__), 'tracks.csv')
    if not os.path.exists(csv_path):
        raise FileNotFoundError("Database file not found.")

    df = pd.read_csv(csv_path)
    query = query.lower()

    mask = df['title'].str.lower().str.contains(query, na=False) |
           df['artist'].str.lower().str.contains(query, na=False)

    return df[mask].to_dict('records')

# Routes
@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'error': 'Empty search query'}), 400

    try:
        results = search_tracks_in_csv(query)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<file_id>', methods=['GET'])
def download(file_id):
    try:
        file_path = download_file(file_id)
        return send_file(file_path, as_attachment=True, mimetype=get_content_type(file_path))
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/stream/<file_id>')
def stream(file_id):
    try:
        session = requests.Session()
        file_url = f"{BASE_EXPORT_URL}{file_id}"
        response = session.get(file_url, stream=True)

        token = get_confirm_token(response)
        if token:
            response = session.get(file_url, params={'confirm': token}, stream=True)

        if response.status_code != 200:
            raise Exception("Failed to fetch file.")

        content_type = response.headers.get('Content-Type', get_content_type(file_id))
        content_length = response.headers.get('Content-Length')
        range_header = request.headers.get('Range')

        if range_header:
            start, end = map(int, range_header.replace('bytes=', '').split('-'))
            headers = {
                'Content-Type': content_type,
                'Content-Range': f'bytes {start}-{end}/{content_length}',
                'Content-Length': str(end - start + 1),
                'Accept-Ranges': 'bytes'
            }
            return Response(response.iter_content(chunk_size=8192), 206, headers=headers, direct_passthrough=True)

        headers = {
            'Content-Type': content_type,
            'Content-Length': content_length,
            'Accept-Ranges': 'bytes'
        }
        return Response(response.iter_content(chunk_size=8192), 200, headers=headers, direct_passthrough=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({'status': 'ok', 'message': 'API is running'})

if __name__ == '__main__':
    app.run(debug=True)
