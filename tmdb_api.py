import requests
import streamlit as st
from rapidfuzz import fuzz

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

    title_lower = title.lower()
    best_score = 0
    best_result = None

    for r in results:
        candidate_title = r.get("title", "").lower()
        score = fuzz.ratio(title_lower, candidate_title)
        if score > best_score:
            best_score = score
            best_result = r

    return best_result, best_score

def get_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
        "append_to_response": "credits"
    }
    response = requests.get(url, params=params)
    return response.json()
