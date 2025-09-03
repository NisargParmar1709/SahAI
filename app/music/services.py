from __future__ import annotations
import json
from datetime import date
from typing import Dict, List, Tuple

CATALOG: Dict[str, List[Dict[str, str]]] = {
    "calm": [
        {"title": "Lo-Fi Study – India", "youtube": "https://www.youtube.com/watch?v=jfKfPfyJRdk", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DXd9rSDyQguIk"},
        {"title": "Instrumental Focus", "youtube": "https://www.youtube.com/watch?v=8m6hHRlKwxY", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX8Uebhn9wzrS"},
        {"title": "Nature Sounds – Monsoon Calm", "youtube": "https://www.youtube.com/watch?v=f77SKdyn-1Y", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX3rxVfibe1L0"},
    ],
    "anxious": [
        {"title": "Breath & Calm (Mantras)", "youtube": "https://www.youtube.com/watch?v=lC8m5_7Zk1Y", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DXaKIA8E7WcJj"},
        {"title": "Soft Indie Uplift", "youtube": "https://www.youtube.com/watch?v=2Vv-BfVoq4g", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX5hR0J49CmXC"},
        {"title": "Gentle Bollywood Chill", "youtube": "https://www.youtube.com/watch?v=8j9zMok6two", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX0XUfTFmNBRM"},
    ],
    "sad": [
        {"title": "Warm Acoustic Hugs", "youtube": "https://www.youtube.com/watch?v=mWRsgZuwf_8", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX3YSRoSdA634"},
        {"title": "Hopeful Bollywood", "youtube": "https://www.youtube.com/watch?v=H5v3kku4y6Q", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWXmlLSKkfdAk"},
        {"title": "Soft Piano for Reflection", "youtube": "https://www.youtube.com/watch?v=1Jfm4Rj9Z0Q", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX4sWSpwq3LiO"},
    ],
    "angry": [
        {"title": "Energy Release (Beats)", "youtube": "https://www.youtube.com/watch?v=2J4O6fGqbU4", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX76Wlfdnj7AP"},
        {"title": "Power Walk Boost", "youtube": "https://www.youtube.com/watch?v=cwQgjq0mCdE", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX0BcQWzuB7ZO"},
        {"title": "Indie Reset", "youtube": "https://www.youtube.com/watch?v=ktvTqknDobU", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX1X23oiQRTB5"},
    ],
    "hopeful": [
        {"title": "Indie Uplift", "youtube": "https://www.youtube.com/watch?v=VbfpW0pbvaU", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX2sUQwD7tbmL"},
        {"title": "Morning Sun – Chill", "youtube": "https://www.youtube.com/watch?v=K4DyBUG242c", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX3rxVfibe1L0"},
        {"title": "Feel-Good Bollywood", "youtube": "https://www.youtube.com/watch?v=JQCP85FngzE", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX0hWmn8d5pRe"},
    ],
    "tired": [
        {"title": "Sleepy Lo-Fi", "youtube": "https://www.youtube.com/watch?v=DWcJFNfaw9c", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWZd79rJ6a7lp"},
        {"title": "Ambient Rest", "youtube": "https://www.youtube.com/watch?v=1ZYbU82GVz4", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWZ7eJRBxKGu0"},
        {"title": "Rainy Night Calm", "youtube": "https://www.youtube.com/watch?v=q76bMs-NwRk", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX3YSRoSdA634"},
    ],
    "focused": [
        {"title": "Deep Focus – India", "youtube": "https://www.youtube.com/watch?v=WpT7x7G7Gq0", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWZeKCadgRdKQ"},
        {"title": "Coding Beats", "youtube": "https://www.youtube.com/watch?v=S4L8T2kFFck", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX8NTLI2TtZa6"},
        {"title": "Minimal Tech Focus", "youtube": "https://www.youtube.com/watch?v=2Q_ZzBGPdqE", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX4sWSpwq3LiO"},
    ],
    "stressed": [
        {"title": "Stress Relief Meditation", "youtube": "https://www.youtube.com/watch?v=inpok4MKVLM", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX3rxVfibe1L0"},
        {"title": "Calm Bollywood Mix", "youtube": "https://www.youtube.com/watch?v=CHekNnySAfM", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWXJfnUiYjUKT"},
    ],
    "motivated": [
        {"title": "Workout Energy", "youtube": "https://www.youtube.com/watch?v=mgmVOuLgFB0", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWY4xHQp97fN6"},
        {"title": "Bollywood Pump", "youtube": "https://www.youtube.com/watch?v=JGwWNGJdvx8", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX76Wlfdnj7AP"},
    ],
    "happy": [
        {"title": "Happy Hits India", "youtube": "https://www.youtube.com/watch?v=kJQP7kiw5Fk", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DXdPec7aLTmlC"},
    ],
    "lonely": [
        {"title": "Alone but Peaceful", "youtube": "https://www.youtube.com/watch?v=s1tAYmMjLdY", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX7qK8ma5wgG1"},
    ],
    "confused": [
        {"title": "Mind Reset Mix", "youtube": "https://www.youtube.com/watch?v=09R8_2nJtjg", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWZqd5JICZI0u"},
    ],
    "grateful": [
        {"title": "Gratitude Vibes", "youtube": "https://www.youtube.com/watch?v=3tmd-ClpJxA", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX2pSTOxoPbx9"},
    ],
    "excited": [
        {"title": "High Energy Mix", "youtube": "https://www.youtube.com/watch?v=OPf0YbXqDm0", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX8FwnYE6PRvL"},
    ],
    "frustrated": [
        {"title": "Chill & Let Go", "youtube": "https://www.youtube.com/watch?v=fLexgOxsZu0", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX9sIqqvKsjG8"},
    ],
    "guilty": [
        {"title": "Forgiveness & Healing", "youtube": "https://www.youtube.com/watch?v=2vjPBrBU-TM", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWVV27DiNWxkR"},
    ],
    "embarrassed": [
        {"title": "Self-Compassion", "youtube": "https://www.youtube.com/watch?v=kXYiU_JCYtU", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWU0ScTcjJBdj"},
    ],
    "insecure": [
        {"title": "Confidence Boost", "youtube": "https://www.youtube.com/watch?v=uelHwf8o7_U", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX0XUfTFmNBRM"},
    ],
    "relieved": [
        {"title": "Peaceful Breathing", "youtube": "https://www.youtube.com/watch?v=R9D-uvKih_k", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DWU13kKnk03AP"},
    ],
    "proud": [
        {"title": "Celebrate Wins", "youtube": "https://www.youtube.com/watch?v=YykjpeuMNEk", "spotify": "https://open.spotify.com/playlist/37i9dQZF1DX1s9knjP51Oa"},
    ],
}

# In-memory simple cache (per-user, per-day, per-mood)
_CACHE: Dict[str, str] = {}


def _cache_key(user_id: int, mood: str) -> str:
    return f"{user_id}:{date.today().isoformat()}:{mood.lower()}"


def get_playlists_for_mood(mood: str, limit: int = 3) -> List[Dict[str, str]]:
    if not mood:
        raise ValueError("mood required")
    m = mood.lower()
    if m not in CATALOG:
        raise ValueError("invalid mood")
    return CATALOG[m][: max(1, min(limit, 3))]


def get_cached_recommendations(user_id: int, mood: str) -> Tuple[bool, Dict]:
    key = _cache_key(user_id, mood)
    if key in _CACHE:
        try:
            return True, json.loads(_CACHE[key])
        except Exception:
            return False, {}
    return False, {}


def set_cached_recommendations(user_id: int, mood: str, payload: Dict) -> None:
    key = _cache_key(user_id, mood)
    _CACHE[key] = json.dumps(payload)
