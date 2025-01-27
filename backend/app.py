from flask import Flask, jsonify, request, send_file, Response
from flask_cors import CORS
import os
from utils.drive_helper import download_file, stream_file, get_drive_service
from utils.csv_helper import search_tracks
from config import TRACKS_CSV_PATH, ensure_data_directories

app = Flask(__name__)
# Fix CORS to handle all methods and headers properly
CORS(app, resources={
    r"/*": {
        "origins": "https://thepathakarpit.github.io",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Range", "Accept", "Accept-Encoding", "Content-Disposition"]
    }
})

# Ensure all required directories exist
ensure_data_directories()

@app.route('/api/search', methods=['GET'])
def search():
    try:
        query = request.args.get('q', '').strip()
        print(f"[Search] Query: '{query}'")
        
        if not query:
            return jsonify({
                'success': True,
                'results': [],
                'count': 0
            })
        
        if not os.path.exists(TRACKS_CSV_PATH):
            print(f"[Error] tracks.csv not found at {TRACKS_CSV_PATH}")
            return jsonify({
                'error': 'Database file not found. Please initialize the database.',
                'path': TRACKS_CSV_PATH
            }), 404
        
        results = search_tracks(query)
        print(f"[Search] Found {len(results)} results")
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        print(f"[Error] Search failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Search failed',
            'message': str(e)
        }), 500

@app.route('/api/download/<file_id>', methods=['GET', 'OPTIONS'])
def download(file_id):
    if request.method == 'OPTIONS':
        return handle_options_request()
        
    try:
        print(f"\n=== Starting download for file_id: {file_id} ===")
        
        # Get file metadata first to get the original filename
        service = get_drive_service()
        file_metadata = service.files().get(fileId=file_id, fields='id,name,mimeType').execute()
        
        if not file_metadata:
            raise Exception("File not found")
            
        filename = file_metadata.get('name', f'{file_id}.flac')
        
        print(f"Streaming file: {filename}")
        file_data = stream_file(file_id)
        
        if not file_data:
            raise Exception("No data received from stream_file")
            
        # Set response headers
        headers = {
            'Access-Control-Allow-Origin': 'https://thepathakarpit.github.io',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Expose-Headers': 'Content-Disposition, Content-Length',
            'Content-Type': 'audio/flac',
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Length': len(file_data)
        }
        
        return Response(
            file_data,
            mimetype='audio/flac',
            headers=headers,
            direct_passthrough=True
        )
        
    except Exception as e:
        print(f"[Error] Download failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/stream/<file_id>', methods=['GET', 'OPTIONS'])
def stream(file_id):
    if request.method == 'OPTIONS':
        return handle_options_request()
        
    try:
        file_data = stream_file(file_id)
        
        if not file_data:
            raise Exception("No data received from stream_file")
        
        headers = {
            'Accept-Ranges': 'bytes',
            'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': 'https://thepathakarpit.github.io',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Range',
            'Access-Control-Expose-Headers': 'Content-Length, Accept-Ranges',
            'Content-Type': 'audio/flac',
            'Content-Length': len(file_data)
        }

        # Handle range requests
        range_header = request.headers.get('Range')
        if range_header:
            bytes_range = range_header.replace('bytes=', '').split('-')
            start = int(bytes_range[0])
            end = int(bytes_range[1]) if bytes_range[1] else len(file_data)
            
            if start >= len(file_data):
                return Response(status=416)  # Range Not Satisfiable
                
            headers['Content-Range'] = f'bytes {start}-{end}/{len(file_data)}'
            return Response(
                file_data[start:end+1],
                status=206,
                mimetype='audio/flac',
                headers=headers
            )

        return Response(
            file_data,
            mimetype='audio/flac',
            headers=headers,
            status=200
        )
    except Exception as e:
        print(f"[Error] Streaming failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/test')
def test():
    try:
        db_exists = os.path.exists(TRACKS_CSV_PATH)
        return jsonify({
            'status': 'ok',
            'message': 'API is running',
            'database_exists': db_exists,
            'database_path': TRACKS_CSV_PATH
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

def handle_options_request():
    headers = {
        'Access-Control-Allow-Origin': 'https://thepathakarpit.github.io',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Range, Accept, Accept-Encoding, Content-Disposition',
        'Access-Control-Max-Age': '3600'
    }
    return ('', 204, headers)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 
