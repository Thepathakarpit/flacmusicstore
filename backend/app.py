from flask import Flask, jsonify, request, send_file, Response, stream_with_context
from flask_cors import CORS
import pandas as pd
import os
from utils.drive_helper import download_file, stream_file
from utils.csv_helper import search_tracks

app = Flask(__name__)
CORS(app, origins=['https://yourusername.github.io'])  # Replace with your GitHub Pages domain

@app.route('/api/search', methods=['GET'])
def search():
    try:
        query = request.args.get('q', '')
        print(f"Searching for: {query}")  # Debug print
        print(f"Current working directory: {os.getcwd()}")
        
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'tracks.csv')
        print(f"Looking for CSV at: {os.path.abspath(csv_path)}")
        
        if not os.path.exists(csv_path):
            print("tracks.csv not found!")  # Debug print
            return jsonify({'error': 'No tracks database found'}), 404
            
        results = search_tracks(query)
        print(f"Found {len(results)} results")  # Debug print
        return jsonify(results)
    except Exception as e:
        print(f"Search error: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500

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
        # Get the file data
        file_data = stream_file(file_id)
        
        # Return as a streaming response
        return Response(
            file_data,
            mimetype='audio/flac',
            headers={
                'Accept-Ranges': 'bytes',
                'Content-Type': 'audio/flac',
                'Cache-Control': 'no-cache'
            }
        )
    except Exception as e:
        print(f"Streaming error: {str(e)}")
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True) 
