# services/tmdb_service.py
import os
import time

import requests
from datetime import datetime, timedelta
from fastapi import APIRouter, Query

from utils.tmdb_util import load_genre, find_genre 

# initialize settings
BEARER = os.getenv("TMDB_BEARER_TOKEN")
IMAGE_BASE = "https://image.tmdb.org/t/p/w500"
GENRE_FILE = "./genres.json"
GENRE_DICT = load_genre(GENRE_FILE, BEARER)

# --- functions ---
def check_validation() -> None:
    url = "https://api.themoviedb.org/3/authentication"
    headers = {
        "accept": "application/json",
        "Authorization": f'''Bearer {BEARER}'''
    }
    response = requests.get(url, headers=headers)
    print(response.text)

def get_upcoming(region: str = "US", page: int = 1) -> dict:
    start_time = time.time()
    url = "https://api.themoviedb.org/3/movie/upcoming"
    params = {
        "language": "en-US",
        "region": region,
        "page": page
    }
    data = _make_request(url, params)
    movies = _process_movies(data.get("results", []))
    elapsed = round(time.time() - start_time, 3)
    return {"elapsed": elapsed, "movies": movies}

def get_upcoming_by_genre(genre_id: str, region: str = "US", page: int = 1) -> dict:
    start_time = time.time()
    url = "https://api.themoviedb.org/3/discover/movie"
    today = datetime.today().date()
    today_after_one_month = today + timedelta(days=30)
    params = {
        "with_genres": genre_id,
        "region": region,
        "include_adult": "false",
        "include_video": "false",
        "language": "en-US",
        "sort_by": "release_date.asc",
        "sort_by": "release_date.asc",
        "release_date.gte": today.strftime("%Y-%m-%d"),
        "release_date.lte": today_after_one_month.strftime("%Y-%m-%d"),
        "with_release_type": "2|3",
        "page": page
    }
    data = _make_request(url, params)
    movies = _process_movies(data.get("results", []))
    elapsed = round(time.time() - start_time, 3)
    return {"elapsed": elapsed, "movies": movies}

# --- support functions ---
def _make_request(url: str, params: dict = None) -> dict:
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {BEARER}"
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def _process_movies(results: list[dict]) -> list[dict]:
    movies = []
    for movie in results:
        movie_genres = []
        for genre_id in movie.get("genre_ids", []):
            movie_genres.append(find_genre(GENRE_DICT, genre_id))
        movies.append({
            "id": movie.get("id", ""),
            "title": movie.get("title", ""),
            "release_date": movie.get("release_date", ""),
            "genres": movie_genres,
            "poster": f"{IMAGE_BASE}{movie.get('poster_path', '')}",
        })
    return movies