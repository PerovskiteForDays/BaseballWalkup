# app.py
import os
import json
import threading
import time
import importlib
from flask import Flask, render_template, jsonify, request
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import roster as roster_module  # your list of players

# === Configuration ===
PLAYLIST_ID = os.getenv("SPOTIPY_PLAYLIST_URI").split(":")[-1]
SAVE_FILE = "saved_assignments.json"
MAX_PLAY_TIME = 30  # seconds

# === Spotify setup ===
sp = Spotify(auth_manager=SpotifyOAuth(
    scope="user-modify-playback-state,user-read-playback-state,playlist-read-private"
))

# === Helper functions ===
def load_saved_data():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_data(data):
    with open(SAVE_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_assignments():
    assignments = load_saved_data()
    # Merge roster
    roster = roster_module.roster
    for player in roster:
        assignments.setdefault(player, {'batting_number': '', 'song': ''})
    return assignments


def get_playlist_songs():
    tracks = []
    results = sp.playlist_tracks(PLAYLIST_ID)
    tracks.extend(results['items'])
    while results.get('next'):
        results = sp.next(results)
        tracks.extend(results['items'])
    return [
        f"{t['track']['name']} – {t['track']['artists'][0]['name']}"
        for t in tracks if t.get('track')
    ]


def build_lineup(assignments, songs):
    lineup = []
    for name, info in assignments.items():
        num = info.get('batting_number', '').strip()
        song = info.get('song', '').strip()
        if num.isdigit() and song in songs:
            lineup.append({'name': name, 'number': int(num), 'song': song})
    return sorted(lineup, key=lambda x: x['number'])

# === Playback ===
def play_track(uri):
    try:
        sp.start_playback(uris=[uri])
    except Exception as e:
        print('Playback error', e)


def fade_stop():
    time.sleep(MAX_PLAY_TIME)
    try:
        sp.pause_playback()
    except:
        pass

# === Flask App ===
app = Flask(__name__)
current_index = 0
songs = get_playlist_songs()
# Initial roster load
roster = roster_module.roster

@app.route('/')
def index():
    assignments = get_assignments()
    return render_template('index.html', roster=roster, assignments=assignments, songs=songs)

@app.route('/api/lineup')
def api_lineup():
    global current_index
    assignments = get_assignments()
    lineup = build_lineup(assignments, songs)
    return jsonify({'lineup': lineup, 'current_index': current_index})

@app.route('/api/next', methods=['POST'])
def api_next():
    global current_index
    assignments = get_assignments()
    lineup = build_lineup(assignments, songs)
    if not lineup:
        return jsonify({'error': 'No lineup'}), 400
    player = lineup[current_index]
    results = sp.search(q=player['song'], type='track', limit=1)
    items = results['tracks']['items']
    if items:
        uri = items[0]['uri']
        play_track(uri)
        threading.Thread(target=fade_stop, daemon=True).start()
    current_index = (current_index + 1) % len(lineup)
    return jsonify({'ok': True})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    try:
        sp.pause_playback()
    except:
        pass
    return jsonify({'ok': True})

@app.route('/api/save', methods=['POST'])
def api_save():
    data = request.json.get('assignments', {})
    roster = roster_module.roster
    for player in roster:
        data.setdefault(player, {'batting_number': '', 'song': ''})
    save_data(data)
    return jsonify({'ok': True})

@app.route('/api/reload', methods=['POST'])
def api_reload():
    global roster
    importlib.reload(roster_module)
    roster = roster_module.roster
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

