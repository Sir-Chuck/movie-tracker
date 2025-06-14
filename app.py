import streamlit as st
import pandas as pd
from tmdb_api import fetch_movie_data
from analytics_tab import render_analytics_tab
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
    render_analytics_tab(df, palette=["#4E79A7", "#F28E2B", "#E15759"])

# Top 100 Tab
elif tab == "Top 100":
    st.title("🏆 MovieGraph: Top 100")
    st.write("Coming soon...")
