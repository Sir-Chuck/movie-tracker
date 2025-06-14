import streamlit as st
import pandas as pd
import os
from datetime import date
from tmdb_api import get_movie_data

# Constants
DATA_PATH = "data/final_movie_data.csv"

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Load or initialize the dataframe
if os.path.exists(DATA_PATH):
    df = pd.read_csv(DATA_PATH)
else:
    df = pd.DataFrame(columns=[
        "Title", "Release Year", "Genre", "Director", "Date Added"
    ])

# App UI
st.title("🎬 Movie Tracker")
st.write("Track your watched movies with rich metadata from TMDB.")

# Add Movies
st.header("➕ Add Movies")
movie_input = st.text_area(
    "Enter movie titles (one per line):",
    placeholder="e.g.\nOppenheimer\nThe Matrix\nLa La Land"
)

if st.button("Add Movies"):
    titles = [title.strip() for title in movie_input.splitlines() if title.strip()]
    added = []
    duplicates = []
    not_found = []
    fuzzy_matches = []

    for title in titles:
        if title.lower() in df["Title"].str.lower().values:
            duplicates.append(title)
            continue

        result = get_movie_data(title)
        if result:
            result["Date Added"] = date.today().isoformat()
            df = pd.concat([df, pd.DataFrame([result])], ignore_index=True)
            added.append(result["Title"])
        else:
            not_found.append(title)

    # Save updated DataFrame
    df.to_csv(DATA_PATH, index=False)

    # Summary
    st.success(f"✅ Added: {', '.join(added) if added else 'None'}")
    st.info(f"🔁 Already tracked: {', '.join(duplicates) if duplicates else 'None'}")
    st.warning(f"❌ Not found: {', '.join(not_found) if not_found else 'None'}")

# Show tracked movies
st.header("📋 Tracked Movies")
if df.empty:
    st.write("No movies tracked yet.")
else:
    st.dataframe(df)

# Reset option
if st.button("🔄 Reset all tracked movies"):
    df = pd.DataFrame(columns=[
        "Title", "Release Year", "Genre", "Director", "Date Added"
    ])
    df.to_csv(DATA_PATH, index=False)
    st.success("All tracked movies have been deleted.")
