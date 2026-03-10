import os
import json
import time
from google import genai
from pydantic import BaseModel, Field
from typing import List, Literal
from dotenv import load_dotenv

load_dotenv()


class MusicConfig:
    MOODS = [
        "Aggressive",
        "Uplifting",
        "Atmospheric",
        "Bittersweet",
        "Melancholic",
        "Empowering",
        "Sensual",
    ]
    GLOBAL_GENRES = [
        "Pop",
        "Rock",
        "Hip-Hop",
        "Electronic",
        "Jazz",
        "Indie",
        "R&B",
        "Metal",
        "Techno",
    ]
    ISRAELI_GENRES = [
        "Mizrahi",
        "Pop",
        "Rock",
        "Ethno-Folk",
        "Chassidic",
        "Hip-Hop",
        "Indie",
    ]


class Playlist(BaseModel):
    name: str = Field(
        description="The category name (e.g., 'Hebrew Mizrahi' or 'Mood: Uplifting')"
    )
    ids: List[str] = Field(description="List of song IDs belonging to this category")


class LibraryClassification(BaseModel):
    playlists: List[Playlist]


PROMPT_TEMPLATE_MOOD = """
You are a professional music curator. Categorize the provided songs into TWO types of buckets.

RULES:
1. MOOD BUCKETS: Use ONLY the mood name from this list: {moods}. 
   Prefix these with 'Mood: '.

SONGS:
{songs_json}
"""

PROMPT_TEMPLATE_GENERE = """
You are a professional music curator. Categorize the provided songs into TWO types of buckets.

RULES:
1. GENRE BUCKETS: Combine the Language + Genre (e.g., "Hebrew Mizrahi", "English Rock"). 
   Use {global_genres} or {israeli_genres} for the genre part.

SONGS:
{songs_json}
"""

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def classify_library(song_list, prompt_template, batch_size=20):
    """Processes songs in batches to avoid AI freezing/timeouts."""
    all_playlists = {}

    for i in range(0, len(song_list), batch_size):
        batch = song_list[i : i + batch_size]
        
        simplified_batch = [{"id": s["id"], "name": s["name"], "artist": s["artist"]} for s in batch]
        
        formatted_prompt = prompt_template.format(
            global_genres=MusicConfig.GLOBAL_GENRES,
            israeli_genres=MusicConfig.ISRAELI_GENRES,
            moods=MusicConfig.MOODS,
            songs_json=json.dumps(simplified_batch),
        )


        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=formatted_prompt,
                    config={
                        "response_mime_type": "application/json",
                        "response_json_schema": LibraryClassification.model_json_schema(),
                    },
                )
                
                if response.text:
                    data = LibraryClassification.model_validate_json(response.text)
                    for p in data.playlists:
                        all_playlists.setdefault(p.name, []).extend(p.ids)
                break 

            except Exception as e:
                if "503" in str(e) and attempt < max_retries - 1:
                    print(f"⚠️ Server busy, retrying batch {i//batch_size + 1} (Attempt {attempt + 1})...")
                    time.sleep(2)
                    continue
                raise e 

        time.sleep(1)

    return {"playlists": [{"name": k, "ids": list(set(v))} for k, v in all_playlists.items()]}

if __name__ == "__main__":
    print("🧪 Testing Gemini Classification...")
    test_songs = [
        {"id": "track_01", "name": "Tel Aviv", "artist": "Omer Adam"},
        {"id": "track_02", "name": "Fix You", "artist": "Coldplay"},
    ]

    res = classify_library(test_songs, PROMPT_TEMPLATE_GENERE)
    print(json.dumps(res, indent=2))
