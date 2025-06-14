# tmdb_api.py
import requests
import streamlit as st
from datetime import datetime

TMDB_BASE_URL = "https://api.themoviedb.org/3"
OMDB_BASE_URL = "http://www.omdbapi.com/"
TMDB_API_KEY = st.secrets["TMDB_API_KEY"]
OMDB_API_KEY = st.secrets["OMDB_API_KEY"]

# U.S. CPI inflation adjustment factor (2024 dollars)
INFLATION_FACTORS = {
    year: 1 + 0.03 * (2024 - year) for year in range(1950, 2025)
}

def adjust_for_inflation(amount, year):
    try:
        year = int(year)
        factor = INFLATION_FACTORS.get(year, 1.0)
        return int(amount * factor)
    except:
        return ""

def fetch_movie_data(title):
    """Search and fetch movie details, director, cast, and financials."""
    search_url = f"{TMDB_BASE_URL}/search/movie"
    search_params = {"api_key": TMDB_API_KEY, "query": title}
    search_resp = requests.get(search_url, params=search_params).json()

    results = search_resp.get("results") or []
    if not results:
        return None

    movie = results[0]
    movie_id = movie["id"]

    # TMDb Details
    detail_url = f"{TMDB_BASE_URL}/movie/{movie_id}"
    detail = requests.get(detail_url, params={"api_key": TMDB_API_KEY}).json()

    # TMDb Credits
    credits_url = f"{TMDB_BASE_URL}/movie/{movie_id}/credits"
    credits = requests.get(credits_url, params={"api_key": TMDB_API_KEY}).json()

    director = next((c["name"] for c in credits.get("crew", []) if c["job"] == "Director"), "")
    cast_list = [c["name"] for c in credits.get("cast", [])][:10]
    cast = ", ".join(cast_list)

    year = detail.get("release_date", "")[:4]
    box_office = detail.get("revenue", 0)
    budget = detail.get("budget", 0)

    adj_box_office = adjust_for_inflation(box_office, year)
    adj_budget = adjust_for_inflation(budget, year)

    # OMDb Call for Metacritic score
    omdb_resp = requests.get(OMDB_BASE_URL, params={"t": title, "apikey": OMDB_API_KEY}).json()
    metacritic = omdb_resp.get("Metascore", "")

    return {
        "Title": detail.get("title"),
        "Year": year,
        "Genre": ", ".join([g["name"] for g in detail.get("genres", [])]),
        "Director": director,
        "Cast": cast,
        "IMDB Rating": detail.get("vote_average"),
        "Runtime": f"{detail.get('runtime')} min" if detail.get("runtime") else "",
        "Language": detail.get("original_language", "").upper(),
        "Overview": detail.get("overview", ""),
        "Box Office": box_office,
        "Box Office (Adj)": adj_box_office,
        "Budget": budget,
        "Budget (Adj)": adj_budget,
        "Metacritic Score": metacritic
    }
