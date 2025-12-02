import os
import random
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Load credentials
load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope="user-read-playback-state user-modify-playback-state playlist-read-private"
))

# Get playlist URI from .env
playlist_uri = os.getenv("SPOTIPY_PLAYLIST_URI")

# Extract playlist ID (strip off 'spotify:playlist:')
playlist_id = playlist_uri.split(":")[-1]

# Get all tracks in the playlist
results = sp.playlist_tracks(playlist_id)
tracks = results['items']

# Optional: continue fetching if playlist has >100 songs
while results['next']:
    results = sp.next(results)
    tracks.extend(results['items'])

# Pick a random song
track = random.choice(tracks)['track']
track_name = track['name']
track_uri = track['uri']
artist = track['artists'][0]['name']

# Play it
devices = sp.devices()
if devices['devices']:
    sp.transfer_playback(devices['devices'][0]['id'], force_play=True)
    sp.start_playback(uris=[track_uri])
    print(f"🎵 Now playing: {track_name} by {artist}")
else:
    print("⚠️ No active devices found. Open Spotify on your phone or computer.")
