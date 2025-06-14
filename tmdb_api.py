# tmdb_api.py
import requests
import streamlit as st
from datetime import datetime

TMDB_BASE_URL = "https://api.themoviedb.org/3"
OMDB_BASE_URL = "http://www.omdbapi.com/"

TMDB_API_KEY = st.secrets["TMDB_API_KEY"]
OMDB_API_KEY = st.secrets.get("OMDB_API_KEY", "")

# U.S. CPI adjustment factor approximation (2024 dollars)
INFLATION_FACTORS = {year: 1 + 0.03 * (2024 - year) for year in range(1950, 2025)}

def adjust_for_inflation(amount, year):
    try:
        year = int(str(year)[:4])
        amount = int(amount)
        factor = INFLATION_FACTORS.get(year, 1.0)
        return int(amount * factor)
    except:
        return ""

def get_metacritic_score(title, year=None):
    try:
        params = {"t": title, "apikey": OMDB_API_KEY}
        if year:
            params["y"] = year

        response = requests.get(OMDB_BASE_URL, params=params).json()
        st.write("🎯 OMDb response:", response)  # Debug

        # Try Ratings first (more reliable)
        for rating in response.get("Ratings", []):
            if rating["Source"] == "Metacritic":
                return rating["Value"].split("/")[0]  # Returns '74' from '74/100'

        # Fallback to Metascore field
        score = response.get("Metascore", "")
        if score and score != "N/A":
            return score
    except Exception as e:
        st.write("❌ OMDb error:", e)
    return ""

def fetch_movie_data(title):
    """Fetch movie data from TMDb and Metacritic from OMDb."""
    search_url = f"{TMDB_BASE_URL}/search/movie"
    search_resp = requests.get(search_url, params={
        "api_key": TMDB_API_KEY,
        "query": title
    }).json()

    results = search_resp.get("results", [])
    if not results:
        return None

    movie = results[0]
    movie_id = movie["id"]

    detail = requests.get(f"{TMDB_BASE_URL}/movie/{movie_id}", params={
        "api_key": TMDB_API_KEY
    }).json()

    credits = requests.get(f"{TMDB_BASE_URL}/movie/{movie_id}/credits", params={
        "api_key": TMDB_API_KEY
    }).json()

    director = next((c["name"] for c in credits.get("crew", []) if c.get("job") == "Director"), "")
    cast_list = [c["name"] for c in credits.get("cast", [])][:10]
    cast = ", ".join(cast_list)

    year = detail.get("release_date", "")[:4]
    box_office = detail.get("revenue", 0)
    budget = detail.get("budget", 0)
    adj_box_office = adjust_for_inflation(box_office, year)
    adj_budget = adjust_for_inflation(budget, year)

    metacritic = get_metacritic_score(title, year)

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
