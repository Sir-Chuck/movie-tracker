import requests
import streamlit as st

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
    title_lower = title.lower()
    for r in results:
        if r["title"].lower() == title_lower:
            return r
    return results[0] if results else None

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
