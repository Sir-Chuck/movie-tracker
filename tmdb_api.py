import requests
from rapidfuzz import fuzz
import streamlit as st

TMDB_API_KEY = st.secrets["tmdb"]["key"]

def search_movie(title):
    url = "https://api.themoviedb.org/3/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "language": "en-US",
        "include_adult": False,
        "page": 1
    }
    response = requests.get(url, params=params)
    return response.json().get("results", [])

def get_best_match(title, results):
    if not results:
        return None, 0
    best_score = 0
    best_result = None
    for r in results:
        score = fuzz.ratio(title.lower(), r.get("title", "").lower())
        if score > best_score:
            best_score = score
            best_result = r
    return best_result, best_score

def get_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {
        "api_key": TMDB_API_KEY,
        "append_to_response": "credits",
        "language": "en-US"
    }
    response = requests.get(url, params=params)
    return response.json()
