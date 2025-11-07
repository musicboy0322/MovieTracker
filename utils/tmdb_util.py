# utils/tmdb_util.py
import os
import json
import requests

def _fetch_genre(genre_file: str, bearer: str) -> bool:
    url = "https://api.themoviedb.org/3/genre/movie/list?language=en"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {bearer}"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return False
        data = response.json()
        with open(genre_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        return False


def load_genre(genre_file: str, bearer: str) -> dict:
    if not os.path.exists(genre_file):
        success = _fetch_genre(genre_file, bearer)
        if not success:
            return {}
    try:
        with open(genre_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            genres = data["genres"]
            genre_dict = {}
            for genre in genres:
                genre_id = genre["id"]
                genre_name = genre["name"]
                genre_dict[genre_id] = genre_name
            return genre_dict
    except Exception as e:
        return {}

def find_genre(genre_dict: dict, genre_id: int) -> str:
    return genre_dict[int(genre_id)]