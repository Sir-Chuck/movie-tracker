import streamlit as st
import pandas as pd
from tmdb_api import get_movie_data
from datetime import datetime
import os

st.set_page_config(page_title="Movie Tracker", layout="wide")

DATA_PATH = "data/tracked_movies.csv"

# Ensure data directory exists
os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)

# Load existing data
if os.path.exists(DATA_PATH):
    df = pd.read_csv(DATA_PATH)
else:
    df = pd.DataFrame(columns=[
        "Title", "Release Year", "Genre", "Director", "Cast", 
        "Runtime", "TMDB Rating", "Date Added"
    ])

st.title("🎬 Movie Tracker")

# Section to add new movies
st.header("➕ Add Movies")
movie_input = st.text_area("Enter movie titles (one per line):", height=200)
if st.button("Add to Tracker"):
    new_movies = [m.strip() for m in movie_input.split("\n") if m.strip()]
    added, skipped, not_found = [], [], []

    for title in new_movies:
        if title in df["Title"].values:
            skipped.append(title)
            continue

        movie_data = get_movie_data(title)
        if movie_data:
            movie_data["Date Added"] = datetime.today().strftime("%Y-%m-%d")
            df = pd.concat([df, pd.DataFrame([movie_data])], ignore_index=True)
            added.append(title)
        else:
            not_found.append(title)

    df.to_csv(DATA_PATH, index=False)

if added:
    st.success(f"✅ Added: {', '.join(added)}")

if skipped:
    st.warning(f"⚠️ Already Tracked: {', '.join(skipped)}")

if not_found:
    st.error(f"❌ Not Found: {', '.join(not_found)}")

# Display tracked movies
st.header("🎞️ Tracked Movies")
st.dataframe(df.sort_values(by="Date Added", ascending=False).reset_index(drop=True), use_container_width=True)
