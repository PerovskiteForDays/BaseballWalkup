from dotenv import load_dotenv
import os

load_dotenv()

print("Client ID:", os.getenv("SPOTIPY_CLIENT_ID"))
print("Secret:", os.getenv("SPOTIPY_CLIENT_SECRET"))
print("Redirect URI:", os.getenv("SPOTIPY_REDIRECT_URI"))