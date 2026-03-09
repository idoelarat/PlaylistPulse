from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse
import urllib.parse
import secrets
import base64
import httpx
import os
import json
import uvicorn
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
redirect_uri = "http://127.0.0.1:8888/callback"
login_uri = "http://127.0.0.1:8888/login"


@app.get("/login")
def login():

    state = secrets.token_urlsafe(16)
    scope = "user-read-private user-library-read playlist-read-private playlist-modify-public playlist-modify-private user-library-modify"

    params = {
        "response_type": "code",
        "client_id": client_id,
        "scope": scope,
        "redirect_uri": redirect_uri,
        "state": state,
    }

    auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(
        params
    )

    return RedirectResponse(auth_url)


@app.get("/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if state is None:
        return RedirectResponse(
            "/#" + urllib.parse.urlencode({"error": "state_mismatch"})
        )

    auth_str = f"{client_id}:{client_secret}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode()

    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    payload = {
        "code": code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        # 1. Exchange code for Access Token
        token_response = await client.post(
            "https://accounts.spotify.com/api/token", data=payload, headers=headers
        )
        tokens = token_response.json()
        access_token = tokens.get("access_token")

        # 2. Fetch data using the new token
        user_headers = {"Authorization": f"Bearer {access_token}"}

        user_response = await client.get(
            "https://api.spotify.com/v1/me", headers=user_headers
        )
        user_data = user_response.json()

        playlist_response = await client.get(
            "https://api.spotify.com/v1/me/playlists?&limit=1",
            headers=user_headers,
        )
        user_playlist = playlist_response.json()

        tracks_response = await client.get(
            "https://api.spotify.com/v1/me/tracks?limit=1", headers=user_headers
        )
        user_tracks = tracks_response.json()

        # 3. Print Basic data to your terminal
        user_name = user_data.get("display_name", "Unknown User")
        user_playlists_total = user_playlist.get("total", 0)
        user_total_saved = user_tracks.get("total", 0)

        print(f"\n🚀 Successfully connected to: {user_name}")
        print(f"📊 Playlists: {user_playlists_total}")
        print(f"🎵 Saved Tracks: {user_total_saved}\n")

        # Save tokens as you did before
        with open(".tokens.json", "w") as f:
            json.dump(tokens, f)

        # Return a simple string instead of HTML
        return HTMLResponse(content="<script>window.close();</script>")


if __name__ == "__main__":
    if not client_id or not client_secret:
        print(
            "Error: SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET not found in environment."
        )
    else:
        print("Starting Spotify connection server on http://127.0.0.1:8888/login")
        uvicorn.run(app, host="127.0.0.1", port=8888)
