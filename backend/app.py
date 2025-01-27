from flask import Flask, jsonify, request, send_file, Response
from flask_cors import CORS
import os
from utils.drive_helper import download_file, stream_file, get_drive_service
from utils.csv_helper import search_tracks
from config import TRACKS_CSV_PATH, ensure_data_directories

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://thepathakarpit.github.io"}})

# Ensure all required directories exist
ensure_data_directories()

@app.route('/api/search', methods=['GET'])
def search():
    try:
        query = request.args.get('q', '').strip()
        print(f"[Search] Query: '{query}'")
        
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
            'error': 'Search failed',
            'message': str(e)
        }), 500

@app.route('/api/download/<file_id>', methods=['GET'])
def download(file_id):
    try:
        print(f"\n=== Starting download for file_id: {file_id} ===")
        
        # Get file metadata first to get the original filename
        service = get_drive_service()
        file_metadata = service.files().get(fileId=file_id, fields='id,name').execute()
        filename = file_metadata.get('name', f'{file_id}.flac')
        
        print("Streaming file data...")
        file_data = stream_file(file_id)
        
        if not file_data:
            raise Exception("No data received from stream_file")
            
        # Set response headers
        headers = {
            'Access-Control-Allow-Origin': 'https://thepathakarpit.github.io',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Expose-Headers': 'Content-Disposition',
            'Content-Type': 'audio/flac',
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        
        return Response(
            file_data,
            mimetype='audio/flac',
            headers=headers,
            direct_passthrough=True
        )
        
    except Exception as e:
        print(f"[Error] Download failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/stream/<file_id>')
def stream(file_id):
    try:
        file_data = stream_file(file_id)
        
        headers = {
            'Accept-Ranges': 'bytes',
            'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': 'https://thepathakarpit.github.io',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Range',
            'Content-Type': 'audio/flac'
        }

        return Response(
            file_data,
            mimetype='audio/flac',
            headers=headers,
            status=200
        )
    except Exception as e:
        print(f"[Error] Streaming failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
        return jsonify({'error': str(e)}), 500

# Add OPTIONS handler for CORS preflight requests
@app.route('/stream/<file_id>', methods=['OPTIONS'])
def stream_options(file_id):
    headers = {
        'Access-Control-Allow-Origin': 'https://thepathakarpit.github.io',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Range',
        'Access-Control-Max-Age': '3600'
    }
    return ('', 204, headers)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 
