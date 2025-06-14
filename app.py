import streamlit as st
import pandas as pd
from tmdb_api import fetch_movie_data
from analytics import render_analytics_tab
from datetime import datetime

st.set_page_config(page_title="MovieGraph", layout="wide")

# Load or initialize data
@st.cache_data
def load_data():
    try:
        return pd.read_csv("movie_data.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            "Title", "Year", "Genre", "Director", "Cast", "Runtime",
            "Budget", "BoxOffice", "FirstWatch", "Rewatchability",
            "Notes", "Added"
        ])

df = load_data()

# Tabs
tab = st.sidebar.radio("Navigation", ["Data Management", "Analytics", "Top 100"])

# Filters (only on Analytics tab)
if tab == "Analytics":
    st.sidebar.markdown("## Filters")
    min_year, max_year = st.sidebar.slider("Year", 1950, datetime.now().year, (2000, datetime.now().year))
    selected_genres = st.sidebar.multiselect("Genre", options=sorted(df["Genre"].dropna().unique()))
    selected_directors = st.sidebar.multiselect("Director", options=sorted(df["Director"].dropna().unique()))

    filtered_df = df[
        (df["Year"].astype(str).str[:4].astype(int).between(min_year, max_year))
    ]

    if selected_genres:
        filtered_df = filtered_df[filtered_df["Genre"].isin(selected_genres)]

    if selected_directors:
        filtered_df = filtered_df[filtered_df["Director"].isin(selected_directors)]
else:
    filtered_df = df.copy()

# Data Management Tab
if tab == "Data Management":
    st.title("🎬 MovieGraph: Data Management")
    st.write("Manage your movie list.")

    with st.form("add_movie_form"):
        title_input = st.text_input("Movie Title")
        year_input = st.text_input("Release Year (optional)")
        submit = st.form_submit_button("Add Movie")

        if submit and title_input:
            movie = fetch_movie_data(title_input, year_input)
            if movie:
                if movie["Title"] not in df["Title"].values:
                    movie["Added"] = datetime.now().strftime("%Y-%m-%d")
                    df = pd.concat([df, pd.DataFrame([movie])], ignore_index=True)
                    df.to_csv("movie_data.csv", index=False)
                    st.success(f"✅ Added: {movie['Title']}")
                else:
                    st.warning("⚠️ Movie already in list.")
            else:
                st.error("❌ Could not find movie.")

    st.dataframe(df)

# Analytics Tab
elif tab == "Analytics":
    st.title("📊 MovieGraph: Analytics")
    render_analytics_tab(filtered_df)

# Top 100 Tab
elif tab == "Top 100":
    st.title("🏆 MovieGraph: Top 100")
    st.write("Coming soon...")

