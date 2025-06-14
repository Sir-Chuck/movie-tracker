import requests
import streamlit as st

TMDB_API_KEY = st.secrets["tmdb"]["key"]

TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_MOVIE_URL = "https://api.themoviedb.org/3/movie/{}"
TMDB_CREDITS_URL = "https://api.themoviedb.org/3/movie/{}/credits"

def get_movie_data(title):
    search_params = {
        "api_key": TMDB_API_KEY,
        "query": title
    }
    search_resp = requests.get(TMDB_SEARCH_URL, params=search_params)

    if search_resp.status_code != 200 or not search_resp.json()["results"]:
        return None

    movie = search_resp.json()["results"][0]
    movie_id = movie["id"]

    # Get more details and credits
    details_resp = requests.get(TMDB_MOVIE_URL.format(movie_id), params={"api_key": TMDB_API_KEY})
    credits_resp = requests.get(TMDB_CREDITS_URL.format(movie_id), params={"api_key": TMDB_API_KEY})

    if details_resp.status_code != 200 or credits_resp.status_code != 200:
        return None

    details = details_resp.json()
    credits = credits_resp.json()

    # Extract director
    director = next((c["name"] for c in credits["crew"] if c["job"] == "Director"), "N/A")

    # Extract top 3 cast members
    cast = [member["name"] for member in credits.get("cast", [])[:3]]
    cast_str = ", ".join(cast)

    return {
        "Title": movie["title"],
        "Release Year": movie.get("release_date", "")[:4],
        "Genre": ", ".join([g["name"] for g in details.get("genres", [])]),
        "Director": director,
        "Cast": cast_str,
        "Runtime": details.get("runtime", "N/A"),
        "TMDB Rating": details.get("vote_average", "N/A")
    }
