import json
import os
import tkinter as tk
from tkinter import ttk
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import threading
import time

# === CONFIGURATION ===
PLAYLIST_ID = "116HUEoHRJLuIvrVXSNTTS"  # Your playlist ID
SAVE_FILE = "saved_assignments.json"
MAX_PLAY_TIME = 30  # seconds

sp = Spotify(auth_manager=SpotifyOAuth(scope="user-modify-playback-state,user-read-playback-state"))

# === FUNCTIONS ===
def load_saved_data(filename=SAVE_FILE):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("⚠️ JSON file is invalid.")
                return {}
    return {}

def save_data(assignments, filename=SAVE_FILE):
    with open(filename, 'w') as f:
        json.dump(assignments, f, indent=2)

def get_playlist_tracks(playlist_id):
    results = sp.playlist_tracks(playlist_id)
    return [item['track']['name'] + " – " + item['track']['artists'][0]['name'] for item in results['items'] if item['track']]

def initialize_roster(saved_data, available_songs):
    roster = []
    for name, info in saved_data.items():
        number = info.get("batting_number")
        song = info.get("song")
        if number and number.strip().isdigit():
            roster.append({
                "name": name,
                "batting_number": int(number.strip()),
                "song": song if song in available_songs else None
            })
    return sorted(roster, key=lambda x: x["batting_number"])

def get_batter_by_order(roster, current_index):
    if not roster:
        return None, None, None
    current = roster[current_index % len(roster)]
    next_ = roster[(current_index + 1) % len(roster)]
    next_next = roster[(current_index + 2) % len(roster)]
    return current, next_, next_next

def play_song(song_name):
    results = sp.search(q=song_name, type='track', limit=1)
    if results['tracks']['items']:
        uri = results['tracks']['items'][0]['uri']
        devices = sp.devices()['devices']
        if devices:
            sp.start_playback(device_id=devices[0]['id'], uris=[uri])
            return True
    return False

def stop_song():
    sp.pause_playback()

# === GUI ===
class WalkupApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Walk-up Song App")

        self.assignments = load_saved_data()
        self.available_songs = get_playlist_tracks(PLAYLIST_ID)
        self.roster = initialize_roster(self.assignments, self.available_songs)
        self.batter_index = 0
        self.playing = False

        self.create_widgets()
        self.update_display()

    def create_widgets(self):
        self.info_label = tk.Label(self.root, text="", font=("Arial", 16))
        self.info_label.pack(pady=10)

        self.next_label = tk.Label(self.root, text="", font=("Arial", 12))
        self.next_label.pack(pady=5)

        self.next_next_label = tk.Label(self.root, text="", font=("Arial", 12))
        self.next_next_label.pack(pady=5)

        self.play_button = ttk.Button(self.root, text="▶️ Next Batter", command=self.play_next_batter)
        self.play_button.pack(pady=10)

        self.stop_button = ttk.Button(self.root, text="⏹️ Stop", command=self.stop_playback)
        self.stop_button.pack(pady=5)

    def update_display(self):
        current, next_, next_next = get_batter_by_order(self.roster, self.batter_index)
        if current:
            self.info_label.config(text=f"Now Playing: {current['name']} (# {current['batting_number']})")
        else:
            self.info_label.config(text="No current batter")

        if next_:
            self.next_label.config(text=f"Next: {next_['name']}")
        else:
            self.next_label.config(text="")

        if next_next:
            self.next_next_label.config(text=f"On Deck: {next_next['name']}")
        else:
            self.next_next_label.config(text="")

    def play_next_batter(self):
        if not self.roster:
            return

        current = self.roster[self.batter_index % len(self.roster)]
        self.update_display()

        if current['song']:
            self.playing = True
            threading.Thread(target=self._play_and_limit_duration, args=(current['song'],)).start()
            self.batter_index = (self.batter_index + 1) % len(self.roster)
        else:
            self.batter_index = (self.batter_index + 1) % len(self.roster)
            self.play_next_batter()

    def _play_and_limit_duration(self, song):
        if play_song(song):
            time.sleep(MAX_PLAY_TIME)
            if self.playing:
                stop_song()
                print(f"⏹️ Stopped after {MAX_PLAY_TIME}s with fade-out.")
        self.playing = False

    def stop_playback(self):
        stop_song()
        self.playing = False
        print("⏹️ Playback manually stopped.")

if __name__ == "__main__":
    root = tk.Tk()
    app = WalkupApp(root)
    root.mainloop()



# import tkinter as tk
# from tkinter import ttk
# import json
# import spotipy
# from spotipy.oauth2 import SpotifyOAuth
# import threading
# import time

# # === Spotify setup ===
# sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="user-modify-playback-state,user-read-playback-state"))

# PLAYLIST_ID = "116HUEoHRJLuIvrVXSNTTS"  # your playlist
# SONG_DURATION = 30  # seconds

# # === Load and Save State ===
# SAVE_FILE = "saved_data.json"

# def load_saved_data():
#     try:
#         with open(SAVE_FILE, "r") as f:
#             data = json.load(f)
#             # Filter valid players with batting number
#             return {
#                 k: v for k, v in data.items()
#                 if v.get("batting_number", "").isdigit() and v.get("song")
#             }
#     except Exception as e:
#         print(f"Could not load saved data: {e}")
#         return {}

# def save_data(data):
#     with open(SAVE_FILE, "w") as f:
#         json.dump(data, f, indent=2)

# # === Get playlist songs ===
# def get_playlist_songs():
#     tracks = sp.playlist_tracks(PLAYLIST_ID)
#     return [f"{item['track']['name']} – {item['track']['artists'][0]['name']}" for item in tracks["items"]]

# # === Playback Control ===
# def play_song(name, song_name):
#     results = sp.search(q=song_name, limit=1, type='track')
#     tracks = results['tracks']['items']
#     if not tracks:
#         print(f"Song not found: {song_name}")
#         return
#     uri = tracks[0]['uri']
#     device_id = sp.devices()['devices'][0]['id']
#     sp.start_playback(device_id=device_id, uris=[uri])
#     print(f"▶️ Playing: {name} → {song_name}")

#     def stop_after_delay():
#         time.sleep(SONG_DURATION)
#         sp.pause_playback(device_id=device_id)
#         print("⏹️ Stopped after 30s with fade-out.")

#     threading.Thread(target=stop_after_delay, daemon=True).start()

# # === GUI ===
# class WalkUpApp:
#     def __init__(self, root):
#         self.root = root
#         root.title("Walk-Up Song App")

#         self.data = load_saved_data()
#         self.playlist_songs = get_playlist_songs()
#         self.lineup = sorted(self.data.items(), key=lambda x: int(x[1]['batting_number']))
#         self.batter_index = 0

#         # Table Headers
#         self.tree = ttk.Treeview(root, columns=("batting", "song"), show="headings", height=10)
#         self.tree.heading("batting", text="Batting #")
#         self.tree.heading("song", text="Assigned Song")
#         self.tree.column("batting", width=100)
#         self.tree.column("song", width=300)
#         self.tree.pack()

#         # Load Data
#         self.update_table()

#         # Info Label
#         self.label = tk.Label(root, text="", font=("Helvetica", 14))
#         self.label.pack(pady=10)

#         # Buttons
#         button_frame = tk.Frame(root)
#         button_frame.pack(pady=10)

#         self.next_btn = tk.Button(button_frame, text="Next Batter", command=self.next_batter)
#         self.next_btn.grid(row=0, column=0, padx=10)

#         self.stop_btn = tk.Button(button_frame, text="Stop", command=self.stop_playback)
#         self.stop_btn.grid(row=0, column=1, padx=10)

#     def update_table(self):
#         for i in self.tree.get_children():
#             self.tree.delete(i)
#         for name, info in self.lineup:
#             self.tree.insert("", "end", values=(info["batting_number"], info["song"]))

#     def update_label(self):
#         if self.batter_index < len(self.lineup):
#             name, info = self.lineup[self.batter_index]
#             next_name, _ = self.lineup[(self.batter_index + 1) % len(self.lineup)]
#             next_next_name, _ = self.lineup[(self.batter_index + 2) % len(self.lineup)]
#             self.label.config(text=f"🎤 Now: {name} (#{info['batting_number']})\n➡️ On Deck: {next_name}\n🔜 In The Hole: {next_next_name}")
#         else:
#             self.label.config(text="✅ All batters complete. Resetting.")

#     def next_batter(self):
#         if self.batter_index >= len(self.lineup):
#             self.batter_index = 0
#         name, info = self.lineup[self.batter_index]
#         song = info["song"]
#         play_song(name, song)
#         self.update_label()
#         self.batter_index += 1

#     def stop_playback(self):
#         try:
#             device_id = sp.devices()['devices'][0]['id']
#             sp.pause_playback(device_id=device_id)
#             print("⏹️ Playback manually stopped.")
#         except:
#             print("⚠️ Could not stop playback.")
#         self.update_label()

# # === Run App ===
# if __name__ == "__main__":
#     root = tk.Tk()
#     app = WalkUpApp(root)
#     root.mainloop()



# # import json
# # import time
# # import threading
# # import tkinter as tk
# # from tkinter import ttk
# # from spotipy.oauth2 import SpotifyOAuth
# # import spotipy

# # # === Spotify Setup ===
# # sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="user-read-playback-state,user-modify-playback-state"))

# # # === Constants ===
# # PLAYLIST_ID = "116HUEoHRJLuIvrVXSNTTS"
# # DATA_FILE = "saved_data.json"

# # # === Load playlist tracks ===
# # def get_playlist_tracks():
# #     results = sp.playlist_tracks(PLAYLIST_ID)
# #     tracks = results["items"]
# #     songs = [
# #         {"name": t["track"]["name"], "artist": t["track"]["artists"][0]["name"]}
# #         for t in tracks if t["track"]
# #     ]
# #     return songs

# # # === Load saved data (assignments) ===
# # def load_saved_data():
# #     try:
# #         with open(DATA_FILE, "r") as f:
# #             return json.load(f)
# #     except:
# #         return {}

# # # === Save data ===
# # def save_data(data):
# #     with open(DATA_FILE, "w") as f:
# #         json.dump(data, f, indent=2)

# # # === Play song helper ===
# # def play_song(song_name):
# #     results = sp.search(q=song_name, type="track", limit=1)
# #     if not results["tracks"]["items"]:
# #         print(f"❌ Song not found: {song_name}")
# #         return
# #     uri = results["tracks"]["items"][0]["uri"]
# #     devices = sp.devices()["devices"]
# #     if not devices:
# #         print("❌ No active Spotify device found.")
# #         return
# #     sp.start_playback(device_id=devices[0]["id"], uris=[uri])
# #     print(f"▶️ Playing: {song_name}")

# #     # Fade out after 30s
# #     def fadeout():
# #         time.sleep(27)
# #         for vol in reversed(range(0, 101, 10)):
# #             try:
# #                 sp.volume(vol)
# #                 time.sleep(0.15)
# #             except:
# #                 break
# #         sp.pause_playback()
# #         print("⏹️ Stopped after 30s with fade-out.")

# #     threading.Thread(target=fadeout).start()

# # # === GUI ===
# # class WalkupApp:
# #     def __init__(self, master):
# #         self.master = master
# #         self.master.title("Walk-Up Song App")

# #         self.songs = get_playlist_tracks()
# #         self.assignments = load_saved_data()
# #         self.batter_index = 0

# #         self.build_gui()
# #         self.refresh_ui()

# #     def build_gui(self):
# #         self.tree = ttk.Treeview(self.master, columns=("Number", "Song"), show='headings')
# #         self.tree.heading("Number", text="Batting #")
# #         self.tree.heading("Song", text="Assigned Song")
# #         self.tree.grid(row=0, column=0, columnspan=4)

# #         self.song_options = [f"{s['name']} – {s['artist']}" for s in self.songs]

# #         self.controls = {}
# #         for i, player in enumerate(sorted(self.assignments.keys())):
# #             row = i + 1
# #             num_var = tk.StringVar(value=self.assignments[player].get("number", ""))
# #             song_var = tk.StringVar(value=self.assignments[player].get("song", ""))

# #             self.controls[player] = (num_var, song_var)

# #         # === Control Buttons ===
# #         tk.Button(self.master, text="Next Batter", command=self.next_batter).grid(row=99, column=0, pady=10)
# #         tk.Button(self.master, text="Stop", command=self.stop_playback).grid(row=99, column=1, pady=10)

# #         self.status_label = tk.Label(self.master, text="")
# #         self.status_label.grid(row=100, column=0, columnspan=4)

# #     def refresh_ui(self):
# #         # Clear tree
# #         for row in self.tree.get_children():
# #             self.tree.delete(row)

# #         # Update data
# #         for player, (num_var, song_var) in self.controls.items():
# #             self.assignments[player]["number"] = int(num_var.get()) if num_var.get().isdigit() else None
# #             self.assignments[player]["song"] = song_var.get()
# #             self.tree.insert("", "end", values=(self.assignments[player]["number"], song_var.get()))

# #         save_data(self.assignments)

# #     def next_batter(self):
# #         # Rebuild lineup with valid numbers
# #         lineup = sorted([
# #             (p, a["number"], a["song"]) for p, a in self.assignments.items()
# #             if isinstance(a.get("number"), int) and a.get("song")
# #         ], key=lambda x: x[1])

# #         if not lineup:
# #             self.status_label.config(text="❌ No valid lineup")
# #             return

# #         self.batter_index = self.batter_index % len(lineup)

# #         current_player, _, song = lineup[self.batter_index]
# #         next_player = lineup[(self.batter_index + 1) % len(lineup)][0]
# #         third_player = lineup[(self.batter_index + 2) % len(lineup)][0]

# #         self.status_label.config(text=f"🎤 Up: {current_player} | On Deck: {next_player} | In Hole: {third_player}")

# #         play_song(song)
# #         self.batter_index += 1

# #     def stop_playback(self):
# #         try:
# #             sp.pause_playback()
# #             self.status_label.config(text=self.status_label.cget("text") + "\n⏹️ Playback manually stopped.")
# #         except:
# #             self.status_label.config(text="❌ Failed to stop playback")

# # # === Run App ===
# # if __name__ == "__main__":
# #     root = tk.Tk()
# #     app = WalkupApp(root)
# #     root.mainloop()




# # # import os
# # # import json
# # # import time
# # # import tkinter as tk
# # # from tkinter import ttk
# # # from dotenv import load_dotenv
# # # import spotipy
# # # from spotipy.oauth2 import SpotifyOAuth
# # # from roster import roster

# # # # === Load .env ===
# # # load_dotenv()

# # # # === Spotify Auth ===
# # # sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
# # #     client_id=os.getenv("SPOTIPY_CLIENT_ID"),
# # #     client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
# # #     redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
# # #     scope="playlist-read-private user-read-playback-state user-modify-playback-state"
# # # ))

# # # # === Playlist Loading ===
# # # playlist_uri = os.getenv("SPOTIPY_PLAYLIST_URI")
# # # playlist_id = playlist_uri.split(":")[-1]

# # # results = sp.playlist_tracks(playlist_id)
# # # tracks = results['items']
# # # while results['next']:
# # #     results = sp.next(results)
# # #     tracks.extend(results['items'])

# # # # Build song list (track name – artist), track URI
# # # song_choices = []
# # # for item in tracks:
# # #     track = item['track']
# # #     name = f"{track['name']} – {track['artists'][0]['name']}"
# # #     uri = track['uri']
# # #     song_choices.append((name, uri))

# # # # === Load/Save Assignment File ===
# # # SAVE_FILE = "saved_assignments.json"

# # # def load_saved_data():
# # #     if os.path.exists(SAVE_FILE):
# # #         try:
# # #             with open(SAVE_FILE, "r") as f:
# # #                 return json.load(f)
# # #         except (json.JSONDecodeError, IOError):
# # #             print("⚠️ Warning: saved_assignments.json is empty or corrupted. Starting fresh.")
# # #             return {}
# # #     return {}


# # # def save_data():
# # #     data = {}
# # #     for player in roster:
# # #         data[player] = {
# # #             "batting_number": batting_vars[player].get(),
# # #             "song": song_vars[player].get()
# # #         }
# # #     with open(SAVE_FILE, "w") as f:
# # #         json.dump(data, f, indent=2)

# # # saved_data = load_saved_data()

# # # # === GUI Setup ===
# # # root = tk.Tk()
# # # root.title("Walk-Up Music App")

# # # # Table headers
# # # headers = ["Player", "Batting #", "Song", "Play"]
# # # for col, h in enumerate(headers):
# # #     ttk.Label(root, text=h, font=("Arial", 10, "bold")).grid(row=0, column=col, padx=5, pady=5)

# # # # Data holders
# # # batting_vars = {}
# # # song_vars = {}

# # # for row, player in enumerate(roster, start=1):
# # #     ttk.Label(root, text=player).grid(row=row, column=0, padx=5, pady=5)

# # #     # Batting #
# # #     b_var = tk.StringVar()
# # #     b_var.set(saved_data.get(player, {}).get("batting_number", ""))
# # #     ttk.Entry(root, textvariable=b_var, width=5).grid(row=row, column=1, padx=5, pady=5)
# # #     batting_vars[player] = b_var

# # #     # Song Dropdown
# # #     s_var = tk.StringVar()
# # #     s_var.set(saved_data.get(player, {}).get("song", ""))
# # #     dropdown = ttk.Combobox(root, textvariable=s_var, width=40, state="readonly")
# # #     dropdown["values"] = [s[0] for s in song_choices]
# # #     dropdown.grid(row=row, column=2, padx=5, pady=5)
# # #     song_vars[player] = s_var

# # #     # Play Button
# # #     def make_play_fn(p):
# # #         return lambda: play_batter(p)
# # #     ttk.Button(root, text="Play", command=make_play_fn(player)).grid(row=row, column=3, padx=5, pady=5)

# # # # === Labels for Batting Order ===
# # # current_batter_label = ttk.Label(root, text="", font=("Arial", 12, "bold"))
# # # current_batter_label.grid(row=len(roster)+1, column=0, columnspan=4, pady=(10, 0))

# # # next_up_label = ttk.Label(root, text="", font=("Arial", 10))
# # # next_up_label.grid(row=len(roster)+2, column=0, columnspan=4)

# # # # === Control Functions ===
# # # current_batter_index = [0]

# # # def update_batter_labels():
# # #     if current_batter_index[0] >= len(roster):
# # #         current_batter_label.config(text="✅ All batters complete.")
# # #         next_up_label.config(text="")
# # #         return

# # #     batter = roster[current_batter_index[0]]
# # #     on_deck = roster[current_batter_index[0] + 1] if current_batter_index[0] + 1 < len(roster) else "—"
# # #     in_hole = roster[current_batter_index[0] + 2] if current_batter_index[0] + 2 < len(roster) else "—"

# # #     batting_num = batting_vars[batter].get() or "?"
# # #     current_batter_label.config(text=f"🎤 Now Batting #{batting_num}: {batter}")
# # #     next_up_label.config(text=f"On Deck: {on_deck}   |   In the Hole: {in_hole}")

# # # def play_batter(batter):
# # #     selected_song = song_vars[batter].get()
# # #     if not selected_song:
# # #         print(f"⚠️ No song selected for {batter}")
# # #         return

# # #     song_uri = next(uri for name, uri in song_choices if name == selected_song)
# # #     batting_num = batting_vars[batter].get() or "?"

# # #     current_batter_label.config(text=f"🎤 Now Batting #{batting_num}: {batter}")
# # #     update_batter_labels()
# # #     save_data()

# # #     devices = sp.devices()
# # #     if not devices['devices']:
# # #         print("⚠️ No active Spotify device found.")
# # #         return

# # #     device_id = devices['devices'][0]['id']
# # #     sp.transfer_playback(device_id, force_play=True)
# # #     sp.start_playback(uris=[song_uri])
# # #     print(f"▶️ Playing: {batter} → {selected_song}")

# # # def stop_playback():
# # #     try:
# # #         sp.pause_playback()
# # #         print("⏹️ Playback manually stopped.")
# # #     except Exception as e:
# # #         print("⚠️ Could not stop playback:", e)

# # # def next_batter():
# # #     if current_batter_index[0] >= len(roster):
# # #         print("✅ All batters complete. Resetting.")
# # #         current_batter_index[0] = 0

# # #     batter = roster[current_batter_index[0]]
# # #     print(f"🎤 Next up: {batter}")
# # #     play_batter(batter)
# # #     current_batter_index[0] += 1
# # #     update_batter_labels()

# # # # === Control Buttons ===
# # # ttk.Button(root, text="Stop", command=stop_playback).grid(row=len(roster)+3, column=0, columnspan=2, pady=10)
# # # ttk.Button(root, text="Next Batter", command=next_batter).grid(row=len(roster)+3, column=2, columnspan=2, pady=10)

# # # # === Init Labels on Load ===
# # # update_batter_labels()

# # # root.mainloop()





# # # # import os
# # # # import time
# # # # import threading
# # # # import tkinter as tk
# # # # from tkinter import ttk
# # # # from dotenv import load_dotenv
# # # # import spotipy
# # # # from spotipy.oauth2 import SpotifyOAuth
# # # # from roster import roster

# # # # # === Load .env ===
# # # # load_dotenv()

# # # # # === Spotify Auth ===
# # # # sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
# # # #     client_id=os.getenv("SPOTIPY_CLIENT_ID"),
# # # #     client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
# # # #     redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
# # # #     scope="playlist-read-private user-read-playback-state user-modify-playback-state"
# # # # ))

# # # # # === Load Playlist Songs ===
# # # # playlist_uri = os.getenv("SPOTIPY_PLAYLIST_URI")
# # # # playlist_id = playlist_uri.split(":")[-1]

# # # # results = sp.playlist_tracks(playlist_id)
# # # # tracks = results['items']
# # # # while results['next']:
# # # #     results = sp.next(results)
# # # #     tracks.extend(results['items'])

# # # # # Create list of (song_name – artist, uri)
# # # # song_choices = []
# # # # for item in tracks:
# # # #     track = item['track']
# # # #     name = f"{track['name']} – {track['artists'][0]['name']}"
# # # #     uri = track['uri']
# # # #     song_choices.append((name, uri))

# # # # # === GUI Setup ===
# # # # root = tk.Tk()
# # # # root.title("Walk-Up Song Player")

# # # # # Table headers
# # # # headers = ["Player", "Batting #", "Song", "Play"]
# # # # for col, h in enumerate(headers):
# # # #     ttk.Label(root, text=h, font=("Arial", 10, "bold")).grid(row=0, column=col, padx=5, pady=5)

# # # # # Track player info
# # # # batting_vars = {}
# # # # song_vars = {}

# # # # # Create rows
# # # # for row, player in enumerate(roster, start=1):
# # # #     ttk.Label(root, text=player).grid(row=row, column=0, padx=5, pady=5)

# # # #     b_var = tk.StringVar()
# # # #     ttk.Entry(root, textvariable=b_var, width=5).grid(row=row, column=1, padx=5, pady=5)
# # # #     batting_vars[player] = b_var

# # # #     s_var = tk.StringVar()
# # # #     dropdown = ttk.Combobox(root, textvariable=s_var, width=40, state="readonly")
# # # #     dropdown['values'] = [s[0] for s in song_choices]
# # # #     dropdown.grid(row=row, column=2, padx=5, pady=5)
# # # #     song_vars[player] = s_var

# # # #     def make_play_fn(p):
# # # #         return lambda: play_batter(p)
# # # #     ttk.Button(root, text="Play", command=make_play_fn(player)).grid(row=row, column=3, padx=5, pady=5)

# # # # # === Controls ===

# # # # current_batter_index = [0]

# # # # # Label for current batter
# # # # current_batter_label = ttk.Label(root, text="", font=("Arial", 12, "bold"))
# # # # current_batter_label.grid(row=len(roster)+1, column=0, columnspan=4, pady=(10, 0))

# # # # # Progress bar
# # # # progress = ttk.Progressbar(root, length=300, mode='determinate', maximum=30)
# # # # progress.grid(row=len(roster)+2, column=0, columnspan=4, pady=10)

# # # # def play_batter(batter):
# # # #     selected_song = song_vars[batter].get()
# # # #     if not selected_song:
# # # #         print(f"⚠️ No song selected for {batter}")
# # # #         return

# # # #     song_uri = next(uri for name, uri in song_choices if name == selected_song)
# # # #     batting_num = batting_vars[batter].get() or "?"
# # # #     current_batter_label.config(text=f"🎤 Now Batting #{batting_num}: {batter}")

# # # #     devices = sp.devices()
# # # #     if not devices['devices']:
# # # #         print("⚠️ No active Spotify device found.")
# # # #         return

# # # #     device_id = devices['devices'][0]['id']
# # # #     sp.transfer_playback(device_id, force_play=True)
# # # #     sp.start_playback(uris=[song_uri])
# # # #     print(f"▶️ Playing: {batter} → {selected_song}")

# # # #     def fade_out_after_30s():
# # # #         try:
# # # #             for t in range(30):
# # # #                 progress["value"] = t + 1
# # # #                 time.sleep(1)
# # # #             for vol in range(100, 30, -10):
# # # #                 sp.volume(vol)
# # # #                 time.sleep(0.5)
# # # #             sp.pause_playback()
# # # #             progress["value"] = 0
# # # #             print("⏹️ Stopped after 30s with fade-out.")
# # # #         except Exception as e:
# # # #             print("⚠️ Fade-out error:", e)
# # # #             progress["value"] = 0

# # # #     threading.Thread(target=fade_out_after_30s, daemon=True).start()

# # # # def stop_playback():
# # # #     try:
# # # #         sp.pause_playback()
# # # #         progress["value"] = 0
# # # #         current_batter_label.config(text="")
# # # #         print("⏹️ Playback manually stopped.")
# # # #     except Exception as e:
# # # #         print("⚠️ Could not stop playback:", e)

# # # # def next_batter():
# # # #     if current_batter_index[0] >= len(roster):
# # # #         print("✅ All batters complete. Resetting.")
# # # #         current_batter_index[0] = 0

# # # #     batter = roster[current_batter_index[0]]
# # # #     print(f"🎤 Next up: {batter}")
# # # #     play_batter(batter)
# # # #     current_batter_index[0] += 1

# # # # # Control buttons
# # # # ttk.Button(root, text="Stop", command=stop_playback).grid(row=len(roster)+3, column=0, columnspan=2, pady=5)
# # # # ttk.Button(root, text="Next Batter", command=next_batter).grid(row=len(roster)+3, column=2, columnspan=2, pady=5)

# # # # root.mainloop()




# # # # # import os
# # # # # import time
# # # # # import threading
# # # # # import tkinter as tk
# # # # # from tkinter import ttk
# # # # # from dotenv import load_dotenv
# # # # # import spotipy
# # # # # from spotipy.oauth2 import SpotifyOAuth
# # # # # from roster import roster

# # # # # # === Load .env ===
# # # # # load_dotenv()

# # # # # # === Spotify Auth ===
# # # # # sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
# # # # #     client_id=os.getenv("SPOTIPY_CLIENT_ID"),
# # # # #     client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
# # # # #     redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
# # # # #     scope="playlist-read-private user-read-playback-state user-modify-playback-state"
# # # # # ))

# # # # # # === Load Playlist Songs ===
# # # # # playlist_uri = os.getenv("SPOTIPY_PLAYLIST_URI")
# # # # # playlist_id = playlist_uri.split(":")[-1]

# # # # # # Load all songs in playlist
# # # # # results = sp.playlist_tracks(playlist_id)
# # # # # tracks = results['items']
# # # # # while results['next']:
# # # # #     results = sp.next(results)
# # # # #     tracks.extend(results['items'])

# # # # # # Build (song name – artist, uri) list
# # # # # song_choices = []
# # # # # for item in tracks:
# # # # #     track = item['track']
# # # # #     name = f"{track['name']} – {track['artists'][0]['name']}"
# # # # #     uri = track['uri']
# # # # #     song_choices.append((name, uri))

# # # # # # === GUI Setup ===
# # # # # root = tk.Tk()
# # # # # root.title("Walk-Up Song Player")

# # # # # # Table headers
# # # # # headers = ["Player", "Batting #", "Song", "Play"]
# # # # # for col, h in enumerate(headers):
# # # # #     ttk.Label(root, text=h, font=("Arial", 10, "bold")).grid(row=0, column=col, padx=5, pady=5)

# # # # # # Data trackers
# # # # # batting_vars = {}
# # # # # song_vars = {}

# # # # # # Table rows
# # # # # for row, player in enumerate(roster, start=1):
# # # # #     ttk.Label(root, text=player).grid(row=row, column=0, padx=5, pady=5)

# # # # #     # Batting number
# # # # #     b_var = tk.StringVar()
# # # # #     ttk.Entry(root, textvariable=b_var, width=5).grid(row=row, column=1, padx=5, pady=5)
# # # # #     batting_vars[player] = b_var

# # # # #     # Song dropdown
# # # # #     s_var = tk.StringVar()
# # # # #     dropdown = ttk.Combobox(root, textvariable=s_var, width=40, state="readonly")
# # # # #     dropdown['values'] = [s[0] for s in song_choices]
# # # # #     dropdown.grid(row=row, column=2, padx=5, pady=5)
# # # # #     song_vars[player] = s_var

# # # # #     # Play button
# # # # #     def make_play_fn(p):
# # # # #         return lambda: play_batter(p)
# # # # #     ttk.Button(root, text="Play", command=make_play_fn(player)).grid(row=row, column=3, padx=5, pady=5)

# # # # # # === Functions ===

# # # # # def play_batter(batter):
# # # # #     selected_song = song_vars[batter].get()
# # # # #     if not selected_song:
# # # # #         print(f"⚠️ No song selected for {batter}")
# # # # #         return

# # # # #     song_uri = next(uri for name, uri in song_choices if name == selected_song)
# # # # #     devices = sp.devices()
# # # # #     if not devices['devices']:
# # # # #         print("⚠️ No active Spotify device found.")
# # # # #         return

# # # # #     device_id = devices['devices'][0]['id']
# # # # #     sp.transfer_playback(device_id, force_play=True)
# # # # #     sp.start_playback(uris=[song_uri])
# # # # #     print(f"▶️ Playing: {batter} → {selected_song}")

# # # # #     def fade_out_after_30s():
# # # # #         time.sleep(27)
# # # # #         try:
# # # # #             for vol in range(100, 30, -10):
# # # # #                 sp.volume(vol)
# # # # #                 time.sleep(0.5)
# # # # #             sp.pause_playback()
# # # # #             print("⏹️ Stopped after 30s with fade-out.")
# # # # #         except Exception as e:
# # # # #             print("⚠️ Fade-out error:", e)

# # # # #     threading.Thread(target=fade_out_after_30s, daemon=True).start()

# # # # # def stop_playback():
# # # # #     try:
# # # # #         sp.pause_playback()
# # # # #         print("⏹️ Manually stopped playback.")
# # # # #     except Exception as e:
# # # # #         print("⚠️ Could not stop playback:", e)

# # # # # # Batting order control
# # # # # current_batter_index = [0]

# # # # # def next_batter():
# # # # #     if current_batter_index[0] >= len(roster):
# # # # #         print("✅ All batters complete. Resetting.")
# # # # #         current_batter_index[0] = 0

# # # # #     batter = roster[current_batter_index[0]]
# # # # #     print(f"🎤 Next up: {batter}")
# # # # #     play_batter(batter)
# # # # #     current_batter_index[0] += 1

# # # # # # === Control Buttons ===
# # # # # ttk.Button(root, text="Stop", command=stop_playback).grid(row=len(roster)+1, column=0, columnspan=2, pady=10)
# # # # # ttk.Button(root, text="Next Batter", command=next_batter).grid(row=len(roster)+1, column=2, columnspan=2, pady=10)

# # # # # root.mainloop()








# # # # # # import os
# # # # # # import tkinter as tk
# # # # # # from tkinter import ttk
# # # # # # from dotenv import load_dotenv
# # # # # # import spotipy
# # # # # # from spotipy.oauth2 import SpotifyOAuth
# # # # # # from roster import roster

# # # # # # # === Load environment variables ===
# # # # # # load_dotenv()

# # # # # # # === Authenticate with Spotify ===
# # # # # # sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
# # # # # #     client_id=os.getenv("SPOTIPY_CLIENT_ID"),
# # # # # #     client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
# # # # # #     redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
# # # # # #     scope="playlist-read-private user-read-playback-state user-modify-playback-state"
# # # # # # ))

# # # # # # # === Load playlist tracks ===
# # # # # # playlist_uri = os.getenv("SPOTIPY_PLAYLIST_URI")
# # # # # # playlist_id = playlist_uri.split(":")[-1]

# # # # # # # Pull all songs
# # # # # # results = sp.playlist_tracks(playlist_id)
# # # # # # tracks = results['items']
# # # # # # while results['next']:
# # # # # #     results = sp.next(results)
# # # # # #     tracks.extend(results['items'])

# # # # # # # Make list of (song_name, uri)
# # # # # # song_choices = []
# # # # # # for item in tracks:
# # # # # #     track = item['track']
# # # # # #     name = f"{track['name']} – {track['artists'][0]['name']}"
# # # # # #     uri = track['uri']
# # # # # #     song_choices.append((name, uri))

# # # # # # # === GUI ===
# # # # # # root = tk.Tk()
# # # # # # root.title("Walk-Up Song Assignment")

# # # # # # # Table headers
# # # # # # headers = ["Player", "Batting #", "Select Song"]
# # # # # # for col, h in enumerate(headers):
# # # # # #     ttk.Label(root, text=h, font=("Arial", 10, "bold")).grid(row=0, column=col, padx=5, pady=5)

# # # # # # # Data tracking
# # # # # # batting_vars = {}
# # # # # # song_vars = {}

# # # # # # # Table rows
# # # # # # for row, player in enumerate(roster, start=1):
# # # # # #     # Player name
# # # # # #     ttk.Label(root, text=player).grid(row=row, column=0, padx=5, pady=5)

# # # # # #     # Batting number entry
# # # # # #     b_var = tk.StringVar()
# # # # # #     entry = ttk.Entry(root, textvariable=b_var, width=5)
# # # # # #     entry.grid(row=row, column=1, padx=5, pady=5)
# # # # # #     batting_vars[player] = b_var

# # # # # #     # Song dropdown
# # # # # #     s_var = tk.StringVar()
# # # # # #     song_dropdown = ttk.Combobox(root, textvariable=s_var, width=40, state="readonly")
# # # # # #     song_dropdown['values'] = [s[0] for s in song_choices]
# # # # # #     song_dropdown.grid(row=row, column=2, padx=5, pady=5)
# # # # # #     song_vars[player] = s_var

# # # # # # # === Play Function ===
# # # # # # def play_selected(player):
# # # # # #     selected_song = song_vars[player].get()
# # # # # #     song_uri = next(uri for name, uri in song_choices if name == selected_song)
# # # # # #     devices = sp.devices()
# # # # # #     if devices['devices']:
# # # # # #         device_id = devices['devices'][0]['id']
# # # # # #         sp.transfer_playback(device_id, force_play=True)
# # # # # #         sp.start_playback(uris=[song_uri])
# # # # # #         print(f"Now playing: {selected_song}")
# # # # # #     else:
# # # # # #         print("⚠️ No active Spotify device found.")

# # # # # # # Play buttons per row
# # # # # # for row, player in enumerate(roster, start=1):
# # # # # #     btn = ttk.Button(root, text="Play", command=lambda p=player: play_selected(p))
# # # # # #     btn.grid(row=row, column=3, padx=5, pady=5)

# # # # # # root.mainloop()
