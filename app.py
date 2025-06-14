import streamlit as st
import pandas as pd
from tmdb_api import search_movie, get_movie_details

# Load existing data
df = pd.read_csv("data/final_movie_data.csv")

st.title("🎬 My Movie Tracker")

# Display movie table
st.subheader("My Watched Movies")
st.dataframe(df)

# Add new movie
st.subheader("➕ Add Movies by Title")
movie_title = st.text_input("Enter movie title")

if st.button("Search & Add"):
    results = search_movie(movie_title)
    if results:
        selected = results[0]
        details = get_movie_details(selected["id"])
        st.json(details)  # For now, show raw data
        # You can later parse and append this to the dataframe
    else:
        st.warning("No results found")
