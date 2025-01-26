import pandas as pd
import os
from config import TRACKS_CSV_PATH

def search_tracks(query):
    try:
        if not os.path.exists(TRACKS_CSV_PATH):
            print(f"CSV file not found at: {TRACKS_CSV_PATH}")
            return []
            
        df = pd.read_csv(TRACKS_CSV_PATH)
        print(f"Loaded {len(df)} tracks from CSV")  # Debug print
        print(f"CSV contents:\n{df}")  # Debug print
        
        if query.strip() == '':
            return df.to_dict('records')  # Return all tracks if query is empty
            
        # Make both query and title lowercase for case-insensitive search
        query = query.lower()
        results = df[df['title'].str.lower().str.contains(query, na=False)]
        print(f"Found {len(results)} matches for '{query}'")  # Debug print
        if len(results) > 0:
            print(f"Matches found:\n{results}")
        return results.to_dict('records')
    except Exception as e:
        print(f"Error in search_tracks: {str(e)}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Looking for CSV at: {os.path.abspath(TRACKS_CSV_PATH)}")
        raise

def update_tracks_index(tracks_data):
    df = pd.DataFrame(tracks_data)
    df.to_csv(TRACKS_CSV_PATH, index=False) 