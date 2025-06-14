import requests
import streamlit as st
from rapidfuzz import process

TMDB_API_KEY = st.secrets["tmdb"]["key"]

def search_tmdb_movie(title):
    url = "https://api.themoviedb.org/3/search/movie"
    params = {"query": title, "api_key": TMDB_API_KEY}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get("results", [])
    return []

def get_best_match(title, results):
    titles = [movie["title"] for movie in results]
    match, score, _ = process.extractOne(title, titles)
    return match if score >= 80 else None

def get_movie_data(title):
    results = search_tmdb_movie(title)

    if not results:
        return {"fuzzy_match": None}

    match_title = get_best_match(title, results)

    if match_title:
        movie = next((m for m in results if m["title"] == match_title), None)
        if movie:
            return {
                "title": movie["title"],
                "release_date": movie.get("release_date", ""),
                "overview": movie.get("overview", ""),
                "vote_average": movie.get("vote_average", ""),
                "tmdb_id": movie.get("id"),
            }
    elif results:
        return {"fuzzy_match": results[0]["title"]}

    return {"fuzzy_match": None}
