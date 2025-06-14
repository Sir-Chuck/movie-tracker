import requests
import streamlit as st

TMDB_API_KEY = st.secrets["tmdb"]["key"]

def get_movie_data(title):
    search_url = "https://api.themoviedb.org/3/search/movie"
    detail_url_base = "https://api.themoviedb.org/3/movie/"

    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
    }

    response = requests.get(search_url, params=params)
    if response.status_code != 200 or not response.json().get("results"):
        return None

    movie = response.json()["results"][0]
    movie_id = movie["id"]

    detail_url = f"{detail_url_base}{movie_id}"
    credits_url = f"{detail_url}/credits"

    detail_params = {"api_key": TMDB_API_KEY}

    detail_resp = requests.get(detail_url, params=detail_params)
    credits_resp = requests.get(credits_url, params=detail_params)

    if detail_resp.status_code != 200:
        return None

    detail_data = detail_resp.json()
    credits_data = credits_resp.json()

    director = ""
    for member in credits_data.get("crew", []):
        if member.get("job") == "Director":
            director = member.get("name")
            break

    genre_names = [g["name"] for g in detail_data.get("genres", [])]

    return {
        "title": movie.get("title"),
        "release_year": movie.get("release_date", "")[:4],
        "genre": ", ".join(genre_names),
        "director": director,
    }
