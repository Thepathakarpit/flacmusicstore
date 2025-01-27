from flask import Flask, jsonify, request, send_file, Response
from flask_cors import CORS
import os
from utils.drive_helper import download_file, stream_file
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
        
        # Verify CSV exists
        if not os.path.exists(TRACKS_CSV_PATH):
            print(f"[Error] tracks.csv not found at {TRACKS_CSV_PATH}")
            return jsonify({
                'error': 'Database file not found. Please initialize the database.',
                'path': TRACKS_CSV_PATH
            }), 404
        
        # Perform search
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
        
        # Add CORS headers for download
        headers = {
            'Access-Control-Allow-Origin': 'https://thepathakarpit.github.io',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Expose-Headers': 'Content-Disposition',
            'Content-Type': 'audio/flac',
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        
        print("Streaming file data...")
        file_data = stream_file(file_id)
        
        print(f"Received file data of size: {len(file_data)} bytes")
        
        if not file_data:
            raise Exception("No data received from stream_file")
            
        print("Creating response...")
        response = Response(
            file_data,
            mimetype='audio/flac',
            headers=headers,
            direct_passthrough=True
        )
        
        print("=== Download process completed successfully ===\n")
        return response
        
    except Exception as e:
        print("\n=== Error in download endpoint ===")
        print(f"Error type: {type(e)}")
        print(f"Error message: {str(e)}")
        print("=== End of error details ===\n")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stream/<file_id>')
def stream(file_id):
    try:
        file_data = stream_file(file_id)
        
        # Add proper CORS and content headers
        headers = {
            'Accept-Ranges': 'bytes',
            'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': 'https://thepathakarpit.github.io',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Range',
            'Content-Type': 'audio/flac'  # Explicitly set content type
        }

        # Handle range requests for seeking
        range_header = request.headers.get('Range')
        if range_header:
            headers['Accept-Ranges'] = 'bytes'
            # Add range handling logic here if needed

        return Response(
            file_data,
            mimetype='audio/flac',
            headers=headers,
            status=200
        )
    except Exception as e:
        print(f"[Error] Streaming failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test', methods=['GET'])
def test():
    try:
        # Test database access
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
@app.route('/api/stream/<file_id>', methods=['OPTIONS'])
def stream_options(file_id):
    headers = {
        'Access-Control-Allow-Origin': 'https://thepathakarpit.github.io',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Range',
        'Access-Control-Max-Age': '3600'
    }
    return ('', 204, headers)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0') 
