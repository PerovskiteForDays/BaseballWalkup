import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope="user-read-playback-state user-modify-playback-state"
))

# === Search for a song ===
results = sp.search(q="Eye of the Tiger", type="track", limit=1)
track_uri = results['tracks']['items'][0]['uri']

# === Transfer playback to active device (if needed) ===
devices = sp.devices()
if devices['devices']:
    device_id = devices['devices'][0]['id']
    sp.transfer_playback(device_id, force_play=True)
else:
    print("⚠️ No active Spotify devices found. Open Spotify on your phone or computer.")
    exit()

# === Start playback ===
sp.start_playback(uris=[track_uri])
print("Now playing: Eye of the Tiger")
