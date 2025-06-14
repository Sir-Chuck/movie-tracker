import requests
import os

TMDB_API_KEY = os.getenv("TMDB_API_KEY")  # Store your key as an environment variable

def search_movie(title):
    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title
    }
    response = requests.get(url, params=params)
    return response.json().get("results", [])

def get_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {"api_key": TMDB_API_KEY, "append_to_response": "credits"}
    response = requests.get(url, params=params)
    return response.json()
