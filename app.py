import os
import pandas as pd
import streamlit as st
from datetime import datetime
from rapidfuzz import fuzz, process
from tmdb_api import get_movie_data

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

DATA_PATH = "data/final_movie_data.csv"

# Load existing data
if os.path.exists(DATA_PATH):
    df = pd.read_csv(DATA_PATH)
else:
    df = pd.DataFrame(columns=["title", "release_year", "genre", "director", "date_added"])

st.title("🎬 Movie Tracker")

# Input section
st.subheader("➕ Add Movies")
movie_input = st.text_area("Enter movie titles (comma or newline separated):")

if st.button("Add to Tracked Movies"):
    titles = [t.strip() for chunk in movie_input.splitlines() for t in chunk.split(",") if t.strip()]
    existing_titles = df["title"].str.lower().tolist()

    added = []
    skipped = []
    not_found = []

    for title in titles:
        if title.lower() in [t.lower() for t in df["title"]]:
            skipped.append(title)
            continue

        movie_data = get_movie_data(title)

        if movie_data:
            if movie_data["title"].lower() in [t.lower() for t in df["title"]]:
                skipped.append(title)
                continue
            movie_data["date_added"] = datetime.today().strftime("%Y-%m-%d")
            df = pd.concat([df, pd.DataFrame([movie_data])], ignore_index=True)
            added.append(movie_data["title"])
        else:
            not_found.append(title)

    df.to_csv(DATA_PATH, index=False)

    st.success(f"✅ Added {len(added)} movie(s).")
    if added:
        st.write("**Added:**", ", ".join(added))
    if skipped:
        st.info(f"⏭️ Skipped (already tracked): {', '.join(skipped)}")
    if not_found:
        st.warning(f"❌ Not found: {', '.join(not_found)}")

# Display section
st.subheader("📊 Tracked Movies")
st.dataframe(df.sort_values(by="date_added", ascending=False).reset_index(drop=True))
