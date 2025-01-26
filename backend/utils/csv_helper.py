import pandas as pd
import os
from config import TRACKS_CSV_PATH

def search_tracks(query):
    """
    Search tracks in the database
    Returns all tracks if query is empty
    """
    try:
        # Verify CSV exists
        if not os.path.exists(TRACKS_CSV_PATH):
            print(f"[Error] CSV file not found at: {TRACKS_CSV_PATH}")
            return []
        
        # Read CSV file
        df = pd.read_csv(TRACKS_CSV_PATH)
        print(f"[Search] Loaded {len(df)} tracks from CSV")
        
        # Return all tracks if query is empty
        if not query:
            return df.to_dict('records')
        
        # Convert query to lowercase for case-insensitive search
        query = query.lower()
        
        # Search across all text columns
        mask = df.apply(lambda x: x.astype(str).str.lower().str.contains(query, na=False)).any(axis=1)
        results = df[mask]
        
        print(f"[Search] Query '{query}' found {len(results)} matches")
        return results.to_dict('records')
        
    except Exception as e:
        print(f"[Error] Search failed: {str(e)}")
        print(f"[Debug] Current directory: {os.getcwd()}")
        print(f"[Debug] CSV path: {os.path.abspath(TRACKS_CSV_PATH)}")
        raise

def update_tracks_index(tracks_data):
    """Update or create the tracks index"""
    try:
        df = pd.DataFrame(tracks_data)
        df.to_csv(TRACKS_CSV_PATH, index=False)
        print(f"[Update] Successfully wrote {len(df)} tracks to CSV")
    except Exception as e:
        print(f"[Error] Failed to update tracks index: {str(e)}")
        raise 
