import json
import requests
import time

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


def sync_playlists(categorized_data):
    headers = get_auth_headers()
    if not headers:
        return print("❌ [bold red]Error:[/] No headers found.")

    final_sync_dict = {}
    if isinstance(categorized_data, dict) and "playlists" in categorized_data:
        for p in categorized_data["playlists"]:
            final_sync_dict[p["name"]] = p["ids"]
    else:
        final_sync_dict = categorized_data

    existing_playlists = {}
    url = "https://api.spotify.com/v1/me/playlists" 
    while url:
        res = requests.get(url, headers=headers).json()
        if "items" in res:
            for pl in res["items"]:
                existing_playlists[pl["name"]] = {
                    "id": pl["id"],
                    "url": pl.get("external_urls", {}).get("spotify")
                }
        url = res.get("next")

    for playlist_name, track_ids in final_sync_dict.items():
        if playlist_name in existing_playlists:
            playlist_id = existing_playlists[playlist_name]["id"]
            playlist_url = existing_playlists[playlist_name]["url"]
            print(f"📂 [bold blue]Found existing:[/] {playlist_name}")
        else:

            create_res = requests.post(
                "https://api.spotify.com/v1/me/playlists",
                headers=headers,
                json={
                    "name": playlist_name,
                    "public": True,
                    "description": "Smartly organized by PlaylistPulse"
                }
            )
            
            if create_res.status_code != 201:
                print(f"❌ Failed to create '{playlist_name}': {create_res.status_code}")
                print(f"   Reason: {create_res.text}")
                continue

            c_data = create_res.json()
            playlist_id = c_data.get("id")
            playlist_url = c_data.get("external_urls", {}).get("spotify")
            print(f"✨ [bold green]Created:[/] {playlist_name}\n🔗 [cyan]Link:[/] {playlist_url}")

        current_tracks = set()
        items_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/items?fields=items(track(id)),next"
        while items_url:
            t_res = requests.get(items_url, headers=headers).json()
            if "items" in t_res:
                for item in t_res["items"]:
                    if item.get("track") and item["track"].get("id"):
                        current_tracks.add(item["track"]["id"])
            items_url = t_res.get("next")

        new_track_uris = [f"spotify:track:{tid}" for tid in track_ids if tid not in current_tracks]

        if new_track_uris:
            for i in range(0, len(new_track_uris), 100):
                batch = new_track_uris[i : i + 100]
                add_res = requests.post(
                    f"https://api.spotify.com/v1/playlists/{playlist_id}/items",
                    headers=headers,
                    json={"uris": batch}
                )
                if add_res.status_code in [200, 201]:
                    print(f"✅ Added {len(batch)} songs to {playlist_name}")
                else:
                    print(f"❌ Failed to add tracks: {add_res.status_code}")