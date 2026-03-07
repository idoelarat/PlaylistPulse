import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

load_dotenv()

scope = "user-library-read"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

results = sp.current_user_saved_tracks(limit=50)
total_tracks = results['total']
all_tracks = []

while results:
    for item in results['items']:
        track = item['track']
        all_tracks.append({
            'id': track['id'],
            'name': track['name'],
            'artist': track['artists'][0]['name']
        })

    print(f"Fetched {len(all_tracks)} / {total_tracks} tracks...", end="\r")
    
    if results['next']:
        results = sp.next(results)
    else:
        results = None

print(f"Successfully fetched {len(all_tracks)} tracks.")