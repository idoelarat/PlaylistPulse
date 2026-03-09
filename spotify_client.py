import json
import requests

def get_auth_headers(token_file=".tokens.json"):
    """Helper to load token and return the required headers."""
    try:
        with open(token_file, 'r') as f:
            tokens = json.load(f)
            access_token = tokens.get("access_token")
            
        return {"Authorization": f"Bearer {access_token}"}
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return None

def get_spotify_user_name():
    headers = get_auth_headers()
    
    if not headers:
        return "Error: Could not retrieve headers."

    url = "https://api.spotify.com/v1/me"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json().get("display_name")
    return f"Failed: {response.status_code}"

if __name__ == "__main__":
    name = get_spotify_user_name()
    
    if "Error" in name or "Failed" in name:
        print(f"❌ Something went wrong: {name}")
    else:
        print(f"✅ Success! Connected to Spotify as: {name}")