import os
import json
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


PROMPT_TEMPLATE = """
You are a professional music curator. Categorize the provided songs into TWO types of buckets.

RULES:
1. GENRE BUCKETS: Combine the Language + Genre (e.g., "Hebrew Mizrahi", "English Rock"). 
   Use {global_genres} or {israeli_genres} for the genre part.
2. MOOD BUCKETS: Use ONLY the mood name from this list: {moods}. 
   Prefix these with 'Mood: '.

SONGS:
{songs_json}
"""

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def classify_library(song_list):
    simplified_songs = [
        {"id": s["id"], "name": s["name"], "artist": s["artist"]} for s in song_list
    ]

    formatted_prompt = PROMPT_TEMPLATE.format(
        global_genres=MusicConfig.GLOBAL_GENRES,
        israeli_genres=MusicConfig.ISRAELI_GENRES,
        moods=MusicConfig.MOODS,
        songs_json=json.dumps(simplified_songs),
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=formatted_prompt,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": LibraryClassification.model_json_schema(),
        },
    )

    raw_json = response.text
    if not raw_json:
        print("⚠️ Warning: Model returned an empty response.")
        return {"playlists": []}

    return LibraryClassification.model_validate_json(raw_json).model_dump()


if __name__ == "__main__":
    print("🧪 Testing Gemini Classification...")
    test_songs = [
        {"id": "track_01", "name": "Tel Aviv", "artist": "Omer Adam"},
        {"id": "track_02", "name": "Fix You", "artist": "Coldplay"},
    ]

    res = classify_library(test_songs)
    print(json.dumps(res, indent=2))
