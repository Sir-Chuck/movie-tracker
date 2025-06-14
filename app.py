# app.py
import os
import pandas as pd
import streamlit as st
from tmdb_api import fetch_movie_data

DATA_FILE = "movies.csv"
REQUIRED_COLUMNS = [
    "Title", "Year", "Genre", "Director", "IMDB Rating",
    "Runtime", "Language", "First Watch", "Rewatchability", "Personal Notes", "Overview"
]

@st.cache_data
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)
    return df

def is_duplicate(entry, df):
    return ((df["Title"] == entry["Title"]) & (df["Year"] == entry["Year"])).any()

def add_movies(titles, df):
    added, skipped, failed = [], [], []
    for title in titles:
        movie = fetch_movie_data(title)
        if not movie:
            failed.append(title)
            continue

        for col in REQUIRED_COLUMNS:
            movie.setdefault(col, "")

        if not is_duplicate(movie, df):
            df = pd.concat([df, pd.DataFrame([movie])], ignore_index=True)
            added.append(title)
        else:
            skipped.append(title)
    return df, added, skipped, failed

def main():
    st.title("🎬 Movie Tracker")
    df = load_data()

    st.header("📥 Add Movies (Batch)")
    titles_input = st.text_area("Enter one movie title per line:")
    if st.button("Add Movies"):
        titles = [t.strip() for t in titles_input.splitlines() if t.strip()]
        df, added, skipped, failed = add_movies(titles, df)
        df.to_csv(DATA_FILE, index=False)
        st.success(f"✅ Added: {len(added)}")
        if skipped:
            st.warning(f"⚠️ Skipped duplicates: {', '.join(skipped)}")
        if failed:
            st.error(f"❌ Not found: {', '.join(failed)}")

    st.header("➕ Add Single Movie")
    title_single = st.text_input("Movie title:")
    if st.button("Add This Movie"):
        if title_single.strip():
            df, added, skipped, failed = add_movies([title_single.strip()], df)
            df.to_csv(DATA_FILE, index=False)
            if added:
                st.success(f"Added: {title_single}")
            elif skipped:
                st.warning("That movie is already in your list.")
            else:
                st.error("Could not find that movie.")

    st.header("🎯 Your Movie Collection")
    st.dataframe(df[REQUIRED_COLUMNS], use_container_width=True)

if __name__ == "__main__":
    main()
