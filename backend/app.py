from flask import Flask, jsonify, request, send_file, Response, session, redirect, url_for
from flask_cors import CORS
import os
from utils.drive_helper import download_file, stream_file, create_flow, get_drive_service
import json

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key')  # Make sure to set this in Railway
CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.route('/api/auth/google')
def google_auth():
    flow = create_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    
    flow = create_flow()
    flow.fetch_token(
        authorization_response=request.url
    )
    
    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    
    return redirect('https://thepathakarpit.github.io/flacmusicstore/')

@app.route('/api/stream/<file_id>')
def stream(file_id):
    try:
        if not get_drive_service():
            return jsonify({'error': 'Not authenticated'}), 401
            
        file_data = stream_file(file_id)
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

@app.route('/api/download/<file_id>')
def download(file_id):
    try:
        if not get_drive_service():
            return jsonify({'error': 'Not authenticated'}), 401
            
        file_path = download_file(file_id)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
