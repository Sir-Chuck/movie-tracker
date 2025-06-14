# tmdb_api.py
import requests
import streamlit as st

TMDB_BASE_URL = "https://api.themoviedb.org/3"
API_KEY = st.secrets["TMDB_API_KEY"]

def fetch_movie_data(title):
    """Search and fetch movie details, director, and top 10 cast from TMDb."""
    search_url = f"{TMDB_BASE_URL}/search/movie"
    search_params = {"api_key": API_KEY, "query": title}
    search_resp = requests.get(search_url, params=search_params).json()

    results = search_resp.get("results") or []
    if not results:
        return None

    movie = results[0]
    movie_id = movie["id"]

    # Fetch movie details
    detail_url = f"{TMDB_BASE_URL}/movie/{movie_id}"
    detail = requests.get(detail_url, params={"api_key": API_KEY}).json()

    # Fetch credits for director and cast
    credits_url = f"{TMDB_BASE_URL}/movie/{movie_id}/credits"
    credits = requests.get(credits_url, params={"api_key": API_KEY}).json()

    director = next((c["name"] for c in credits.get("crew", []) if c["job"] == "Director"), "")
    cast_list = [c["name"] for c in credits.get("cast", [])][:10]
    cast = ", ".join(cast_list)

    return {
        "Title": detail.get("title"),
        "Year": detail.get("release_date", "")[:4],
        "Genre": ", ".join([g["name"] for g in detail.get("genres", [])]),
        "Director": director,
        "Cast": cast,
        "IMDB Rating": detail.get("vote_average"),
        "Runtime": f"{detail.get('runtime')} min" if detail.get("runtime") else "",
        "Language": detail.get("original_language", "").upper(),
        "Overview": detail.get("overview", "")
    }
