import streamlit as st
import pandas as pd
from datetime import datetime
from tmdb_api import get_movie_data

st.set_page_config(page_title="🎬 Movie Tracker", layout="wide")
st.title("🎬 Movie Tracker")

DATA_PATH = "tracked_movies.csv"

# Load or initialize data
try:
    df = pd.read_csv(DATA_PATH)
except FileNotFoundError:
    df = pd.DataFrame(columns=[
        "title", "release_year", "genre", "director", "cast", "date_added"
    ])

# Display tracked movies
st.subheader("Currently Tracked Movies")
st.dataframe(df.sort_values(by="date_added", ascending=False), use_container_width=True)

# Add new movies
st.subheader("➕ Add Movies")
with st.form("add_movies"):
    new_movies_input = st.text_area("Enter movie titles (one per line):")
    submitted = st.form_submit_button("Add to Tracked List")

    if submitted:
        new_movies = [m.strip() for m in new_movies_input.strip().split("\n") if m.strip()]
        added = []
        skipped = []
        not_found = []

        for title in new_movies:
            if title.lower() in df['title'].str.lower().values:
                skipped.append(title)
                continue

            movie_data = get_movie_data(title)
            if movie_data:
                movie_data["date_added"] = datetime.today().strftime("%Y-%m-%d")
                df = pd.concat([df, pd.DataFrame([movie_data])], ignore_index=True)
                added.append(title)
            else:
                not_found.append(title)

        df.to_csv(DATA_PATH, index=False)

        # Display results without returning DeltaGenerator
        if added:
            st.success("✅ Added: " + ", ".join(added))
        if skipped:
            st.warning("⚠️ Already Tracked: " + ", ".join(skipped))
        if not_found:
            st.error("❌ Not Found: " + ", ".join(not_found))
