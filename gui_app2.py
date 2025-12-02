import json
import os
import tkinter as tk
from tkinter import ttk
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import time

# === CONFIGURATION ===
PLAYLIST_ID = "116HUEoHRJLuIvrVXSNTTS"  # Your playlist ID
SAVE_FILE = "saved_assignments.json"
MAX_PLAY_TIME = 30  # seconds

# Spotify client setup
sp = Spotify(auth_manager=SpotifyOAuth(scope="user-modify-playback-state,user-read-playback-state"))

# === FUNCTIONS ===

def load_saved_data(filename=SAVE_FILE):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("⚠️ JSON file is invalid. Starting fresh.")
    return {}


def save_data(assignments, filename=SAVE_FILE):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(assignments, f, indent=2, ensure_ascii=False)


def get_playlist_tracks(playlist_id):
    results = sp.playlist_tracks(playlist_id)
    return [
        item['track']['name'] + " – " + item['track']['artists'][0]['name']
        for item in results['items'] if item.get('track')
    ]


def build_lineup(assignments, available_songs):
    lineup = []
    for name, info in assignments.items():
        num = info.get('batting_number', '').strip()
        song = info.get('song', '').strip()
        if num.isdigit() and song in available_songs:
            lineup.append({'name': name, 'batting_number': int(num), 'song': song})
    return sorted(lineup, key=lambda x: x['batting_number'])


def fetch_devices():
    return sp.devices().get('devices', [])


def ensure_device(device_id):
    # Transfer playback to selected device
    try:
        sp.transfer_playback(device_id=device_id, force_play=True)
    except Exception as e:
        print(f"⚠️ Could not transfer playback: {e}")


def play_song(song_name, device_id=None):
    # Ensure correct device
    if device_id:
        ensure_device(device_id)
    res = sp.search(q=song_name, type='track', limit=1)
    items = res['tracks']['items']
    if not items:
        print(f"❌ Song not found: {song_name}")
        return False
    uri = items[0]['uri']
    try:
        # Play on specified device or current active
        if device_id:
            sp.start_playback(device_id=device_id, uris=[uri])
        else:
            sp.start_playback(uris=[uri])
        return True
    except Exception as e:
        print(f"❌ Playback error: {e}")
        return False


def stop_song(device_id=None):
    try:
        if device_id:
            sp.pause_playback(device_id=device_id)
        else:
            sp.pause_playback()
    except Exception as e:
        print(f"⚠️ Could not stop playback: {e}")

# === GUI ===
class WalkupApp:
    def __init__(self, root):
        self.root = root
        root.title("Walk-up Song App")

        self.assignments = load_saved_data()
        self.available_songs = get_playlist_tracks(PLAYLIST_ID)
        self.batter_index = 0
        self.playing = False
        self.device_id = None

        self.create_widgets()
        self.update_device_list()
        self.update_display()

    def create_widgets(self):
        # Device selector
        dev_frame = ttk.Frame(self.root)
        dev_frame.pack(pady=5)
        ttk.Label(dev_frame, text="Select Device:").grid(row=0, column=0)
        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(dev_frame, textvariable=self.device_var,
                                         state='readonly', width=30)
        self.device_combo.grid(row=0, column=1, padx=5)
        self.device_combo.bind("<<ComboboxSelected>>", self.on_device_select)
        ttk.Button(dev_frame, text="Refresh", command=self.update_device_list).grid(row=0, column=2)

        # Status labels
        self.info_label = ttk.Label(self.root, text="", font=("Arial", 16, "bold"))
        self.info_label.pack(pady=(10,5))
        self.next_label = ttk.Label(self.root, text="", font=("Arial", 12))
        self.next_label.pack()
        self.next_next_label = ttk.Label(self.root, text="", font=("Arial", 12))
        self.next_next_label.pack(pady=(0,10))

        # Control buttons
        ctrl_frame = ttk.Frame(self.root)
        ctrl_frame.pack(pady=5)
        ttk.Button(ctrl_frame, text="▶️ Next Batter", command=self.play_next_batter).grid(row=0, column=0, padx=5)
        ttk.Button(ctrl_frame, text="⏹️ Stop", command=self.stop_playback).grid(row=0, column=1, padx=5)

        # Roster table
        table_frame = ttk.Frame(self.root)
        table_frame.pack(padx=10, pady=10)
        headers = ["Player", "Batting #", "Song"]
        for col, h in enumerate(headers):
            ttk.Label(table_frame, text=h, font=("Arial", 10, "bold")).grid(row=0, column=col, padx=5)

        self.batting_vars = {}
        self.song_vars = {}
        max_num = len(self.available_songs)
        for r, name in enumerate(self.assignments.keys(), start=1):
            info = self.assignments[name]
            ttk.Label(table_frame, text=name).grid(row=r, column=0, padx=5)
            bvar = tk.StringVar(value=info.get('batting_number', 'Not in lineup'))
            bcombo = ttk.Combobox(table_frame, textvariable=bvar, state='readonly', width=12)
            bcombo['values'] = ['Not in lineup'] + [str(i) for i in range(1, max_num+1)]
            bcombo.grid(row=r, column=1, padx=5)
            bvar.trace_add('write', lambda *a, p=name: self.on_assign(p))
            self.batting_vars[name] = bvar

            svar = tk.StringVar(value=info.get('song', ''))
            scombo = ttk.Combobox(table_frame, textvariable=svar, state='readonly', width=40)
            scombo['values'] = self.available_songs
            scombo.grid(row=r, column=2, padx=5)
            svar.trace_add('write', lambda *a, p=name: self.on_assign(p))
            self.song_vars[name] = svar

    def update_device_list(self):
        devices = fetch_devices()
        names = [d['name'] for d in devices]
        self.device_map = {d['name']: d['id'] for d in devices}
        self.device_combo['values'] = names
        if names:
            self.device_var.set(names[0])
            self.device_id = self.device_map[names[0]]

    def on_device_select(self, event=None):
        self.device_id = self.device_map.get(self.device_var.get())

    def on_assign(self, player):
        self.assignments[player] = {
            'batting_number': self.batting_vars[player].get(),
            'song': self.song_vars[player].get()
        }
        save_data(self.assignments)

    def update_display(self):
        lineup = build_lineup(self.assignments, self.available_songs)
        if lineup:
            idx = self.batter_index % len(lineup)
            curr = lineup[idx]
            nxt = lineup[(idx+1) % len(lineup)]
            n2 = lineup[(idx+2) % len(lineup)]
            self.info_label.config(text=f"Now: {curr['name']} (#{curr['batting_number']})")
            self.next_label.config(text=f"On Deck: {nxt['name']}")
            self.next_next_label.config(text=f"In The Hole: {n2['name']}")
        else:
            self.info_label.config(text="No valid lineup")
            self.next_label.config(text="")
            self.next_next_label.config(text="")

    def play_next_batter(self):
        lineup = build_lineup(self.assignments, self.available_songs)
        if not lineup or not self.device_id:
            return
        idx = self.batter_index % len(lineup)
        curr = lineup[idx]
        self.update_display()
        if curr['song'] and play_song(curr['song'], self.device_id):
            self.playing = True
            self.root.after(MAX_PLAY_TIME * 1000, self.auto_stop)
        self.batter_index = (self.batter_index + 1) % len(lineup)

    def auto_stop(self):
        if self.playing:
            stop_song(self.device_id)
            print(f"⏹️ Auto-stopped after {MAX_PLAY_TIME}s.")
            self.playing = False
            self.update_display()

    def stop_playback(self):
        if self.device_id:
            stop_song(self.device_id)
            self.playing = False
            print("⏹️ Playback manually stopped.")
            self.update_display()

if __name__ == '__main__':
    root = tk.Tk()
    app = WalkupApp(root)
    root.mainloop()
