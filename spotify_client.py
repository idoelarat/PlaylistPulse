import json
import requests


def get_auth_headers(token_file=".tokens.json"):
    """Helper to load token and return the required headers."""
    try:
        with open(token_file, "r") as f:
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


def get_total_saved_songs():
    headers = get_auth_headers()
    if not headers:
        return "Error: Could not retrieve headers."

    url = "https://api.spotify.com/v1/me/tracks"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json().get("total")
    return f"Failed: {response.status_code}"


def all_saved_songs():
    headers = get_auth_headers()
    if not headers:
        return "Error: Could not retrieve headers."

    url = "https://api.spotify.com/v1/me/tracks?limit=50"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return f"Error: {response.status_code}"

    data = response.json()

    song_list = []

    while url:
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            break

        data = response.json()
        items = data.get("items", [])

        for item in items:
            track = item.get("track")
            if track:
                song_list.append(
                    {
                        "id": track["id"],
                        "name": track["name"],
                        "artist": track["artists"][0]["name"],
                    }
                )

        url = data.get("next")

    return song_list


if __name__ == "__main__":
    name = get_spotify_user_name()

    if "Error" in name or "Failed" in name:
        print(f"❌ Something went wrong: {name}")
    else:
        print(f"✅ Success! Connected to Spotify as: {name}")
