# FLAC Music Store

Visit the live site: https://Thepathakarpit.github.io/flacmusicstore/frontend/

## Development

1. Clone the repository
2. Set up the backend (see backend/README.md)
3. Run the frontend locally:
   ```bash
   cd frontend
   python -m http.server 8000
   ```

## Features
- Search music tracks by title
- Direct download links for FLAC files
- Google Drive integration for storage
- CSV-based track indexing

## Project Structure
```
/flac
├── backend/
│   ├── app.py                 # Flask backend server
│   ├── config.py              # Configuration settings
│   ├── requirements.txt       # Python dependencies
│   └── utils/
│       ├── drive_helper.py    # Google Drive API functions
│       └── csv_helper.py      # CSV operations
├── frontend/
│   ├── index.html            # Main page
│   ├── css/
│   │   └── style.css         # Styling
│   └── js/
│       └── main.js           # Frontend logic
├── data/
│   └── tracks.csv            # Track metadata and Drive IDs
└── README.md                 # Project documentation
```

## Setup Instructions

### 1. Google Drive Setup
1. Create a new Gmail account for storing FLAC files (e.g., flacmusicstorehah@gmail.com)
2. Go to [Google Cloud Console](https://console.cloud.google.com/)
3. Create a new project
4. Enable the Google Drive API for your project
5. Configure OAuth consent screen
6. Create OAuth 2.0 Client ID credentials
7. Download the credentials and save as `credentials.json` in the backend directory
8. Note down your Google Drive folder ID where FLAC files are stored

### 2. Backend Setup
```bash
# Create and activate virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Update config.py
# Replace 'your_folder_id' with your actual Google Drive folder ID
```

### 3. Frontend Setup
No additional setup required for frontend files.

### 4. Running the Application

Start the backend server:
```bash
cd backend
python app.py
```

Start the frontend server (in a new terminal):
```bash
cd frontend
python -m http.server 8000
```
