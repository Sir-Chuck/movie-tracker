# app.py
import os
import pandas as pd
import streamlit as st
from datetime import datetime
from tmdb_api import fetch_movie_data

DATA_FILE = "movies.csv"
REQUIRED_COLUMNS = [
    "Title", "Year", "Genre", "Director", "Cast", "IMDB Rating",
    "Runtime", "Language", "Overview", "Date Added"
]

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[REQUIRED_COLUMNS]

def is_duplicate(entry, df):
    title = entry["Title"].strip().lower()
    year = str(entry["Year"]).strip()

    df_check = df.copy()
    df_check["Title"] = df_check["Title"].fillna("").str.strip().str.lower()
    df_check["Year"] = df_check["Year"].fillna("").astype(str).str.strip()

    return ((df_check["Title"] == title) & (df_check["Year"] == year)).any()

def add_movies(titles, df):
    added, skipped, failed = [], [], []
    progress = st.progress(0, text="⏳ Fetching movies...")

    total = len(titles)
    for i, title in enumerate(titles):
        progress.progress((i + 1) / total, text=f"Fetching: {title} ({i+1}/{total})")

        movie = fetch_movie_data(title)
        if not movie:
            failed.append(title)
            continue

        movie["Date Added"] = datetime.today().strftime("%Y-%m-%d")
        for col in REQUIRED_COLUMNS:
            movie.setdefault(col, "")

        if not is_duplicate(movie, df):
            df = pd.concat([df, pd.DataFrame([movie])], ignore_index=True)
            added.append(title)
        else:
            skipped.append(title)

    progress.empty()
    return df, added, skipped, failed

def main():
    st.title("🎬 Movie Tracker")

    df = load_data()

    st.header("📥 Add Movies (Batch)")
    titles_input = st.text_area("Enter one movie title per line:")
    if st.button("Add Movies"):
        titles = [t.strip() for t in titles_input.splitlines() if t.strip()]
        if titles:
            df, added, skipped, failed = add_movies(titles, df)
            df.to_csv(DATA_FILE, index=False)

            st.success(f"✅ Added: {len(added)} movies")
            if skipped:
                st.info(f"⏭️ Skipped (already in collection): {len(skipped)}")
            if failed:
                st.error(f"❌ Not found in TMDb: {len(failed)}")

    st.header("➕ Add Single Movie")
    title_single = st.text_input("Movie title:")
    if st.button("Add This Movie"):
        if title_single.strip():
            df, added, skipped, failed = add_movies([title_single.strip()], df)
            df.to_csv(DATA_FILE, index=False)

            if added:
                st.success(f"✅ Added: {title_single}")
            elif skipped:
                st.info("⏭️ Skipped: already in collection")
            elif failed:
                st.error("❌ Could not find that movie")

    st.header("🧼 Data Management")
    if "data_cleared" not in st.session_state:
        st.session_state["data_cleared"] = False
    
    if st.button("❌ Clear All Movie Data"):
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)
        df.to_csv(DATA_FILE, index=False)
        st.session_state["data_cleared"] = True
        st.success("All movie data has been cleared. Reloading...")
    
    # Trigger rerun after clearing
    if st.session_state["data_cleared"]:
        st.session_state["data_cleared"] = False
        st.stop()  # Safe way to end and refresh the session

    st.header("🎯 Your Movie Collection")
    st.dataframe(df[REQUIRED_COLUMNS], use_container_width=True)

if __name__ == "__main__":
    main()
