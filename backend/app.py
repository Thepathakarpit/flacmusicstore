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
        file_path = download_file(file_id)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/stream/<file_id>')
def stream(file_id):
    try:
        file_data = stream_file(file_id)
        return Response(
            file_data,
            mimetype='audio/flac',
            headers={
                'Accept-Ranges': 'bytes',
                'Cache-Control': 'no-cache'
            }
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0') 
