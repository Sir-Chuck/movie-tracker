# app.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime
from tmdb_api import fetch_movie_data
from analytics_tab import analytics_tab

st.set_page_config(page_title="MovieGraph", layout="wide")

BACKEND_PATH = "data/backend_movie_data.csv"
REQUIRED_COLUMNS = [
    "Title", "Rank", "Year", "Genre", "Director", "Cast",
    "IMDB Rating", "Rotten Tomatoes", "Metacritic Score", "Awards",
    "Runtime", "Language", "Overview",
    "Box Office", "Box Office (Adj)", "Budget", "Budget (Adj)", "Date Added"
]

# Ensure data directory exists
if not os.path.exists("data"):
    os.makedirs("data")

def load_data():
    if os.path.exists(BACKEND_PATH):
        return pd.read_csv(BACKEND_PATH)
    return pd.DataFrame(columns=REQUIRED_COLUMNS)

def save_data(df):
    df.to_csv(BACKEND_PATH, index=False)

def data_management_tab():
    st.subheader("Add Movies to Your Collection")
    title_input = st.text_area("Enter movie titles (one per line):")
    if st.button("Add Movies"):
        if title_input.strip():
            movie_titles = [title.strip() for title in title_input.strip().split("\n") if title.strip()]
            existing_df = load_data()
            with st.spinner("Fetching movie data..."):
                progress_bar = st.progress(0)
                new_movies, skipped, not_found = [], [], []
                for i, title in enumerate(movie_titles):
                    if title in existing_df["Title"].values:
                        skipped.append(title)
                        continue
                    data = fetch_movie_data(title)
                    if data:
                        new_movies.append(data)
                    else:
                        not_found.append(title)
                    progress_bar.progress((i + 1) / len(movie_titles))
            if new_movies:
                df_new = pd.DataFrame(new_movies)
                df_new["Date Added"] = datetime.now().strftime("%Y-%m-%d")
                updated_df = pd.concat([existing_df, df_new], ignore_index=True)
                save_data(updated_df)
                st.success(f"Added {len(new_movies)} movies. Skipped: {len(skipped)}. Not found: {len(not_found)}")
                if skipped:
                    st.warning(f"Skipped: {', '.join(skipped)}")
                if not_found:
                    st.error(f"Not found: {', '.join(not_found)}")
            else:
                st.info("No new movies were added.")

    if st.button("Clear All Data"):
        if os.path.exists(BACKEND_PATH):
            os.remove(BACKEND_PATH)
            st.success("All movie data cleared.")

    df = load_data()
    st.subheader("Your Movie Collection")
    st.write(f"Total Movies: {len(df)}")
    st.dataframe(df.sort_values("Date Added", ascending=False), use_container_width=True)
    return df

def top_100_tab():
    st.subheader("Top 100")
    st.info("Top 100 movie ranking functionality will be added here.")

# Set up main navigation tabs
tabs = st.tabs(["Data Management", "Analytics", "Top 100"])

with tabs[0]:
    df = data_management_tab()

with tabs[1]:
    analytics_tab(df)

with tabs[2]:
    top_100_tab()
