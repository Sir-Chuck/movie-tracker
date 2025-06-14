import requests
import os
from datetime import datetime

TMDB_API_KEY = os.getenv("TMDB_API_KEY") or "your_tmdb_api_key_here"
TMDB_BASE_URL = "https://api.themoviedb.org/3"

def search_movie(title):
    url = f"{TMDB_BASE_URL}/search/movie"
    params = {"api_key": TMDB_API_KEY, "query": title}
    response = requests.get(url, params=params)
    response.raise_for_status()
    results = response.json().get("results", [])
    return results[0] if results else None

def get_movie_details(movie_id):
    url = f"{TMDB_BASE_URL}/movie/{movie_id}"
    params = {"api_key": TMDB_API_KEY}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def get_movie_credits(movie_id):
    url = f"{TMDB_BASE_URL}/movie/{movie_id}/credits"
    params = {"api_key": TMDB_API_KEY}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def fetch_movie_data(title):
    result = search_movie(title)
    if not result:
        return None

    movie_id = result["id"]
    details = get_movie_details(movie_id)
    credits = get_movie_credits(movie_id)

    directors = [person["name"] for person in credits["crew"] if person["job"] == "Director"]
    cast = [actor["name"] for actor in credits["cast"][:3]]
    genres = [genre["name"] for genre in details.get("genres", [])]

    return {
        "title": details.get("title"),
        "release_year": details.get("release_date", "")[:4],
        "genres": ", ".join(genres),
        "director": ", ".join(directors),
        "cast": ", ".join(cast),
        "overview": details.get("overview"),
        "date_added": datetime.today().strftime("%Y-%m-%d"),
    }
