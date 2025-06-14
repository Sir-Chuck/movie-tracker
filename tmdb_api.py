import requests
import streamlit as st
from rapidfuzz import fuzz

RAPIDAPI_KEY = st.secrets["rapidapi"]["key"]
RAPIDAPI_HOST = st.secrets["rapidapi"]["host"]

def search_movie(title):
    url = "https://api.themoviedb.org/3/search/movie"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }
    params = {
        "query": title,
        "include_adult": False,
        "language": "en-US",
        "page": 1
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json().get("results", [])

def get_best_match(title, results):
    if not results:
        return None

    title_lower = title.lower()
    best_score = 0
    best_result = None

    for r in results:
        candidate_title = r.get("title", "").lower()
        score = fuzz.ratio(title_lower, candidate_title)
        if score > best_score:
            best_score = score
            best_result = r

    return best_result if best_score > 60 else None  # Adjustable threshold

def get_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }
    params = {
        "language": "en-US",
        "append_to_response": "credits"
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()
