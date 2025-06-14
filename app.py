# app.py
import streamlit as st
import pandas as pd
from datetime import datetime
from tmdb_api import fetch_movie_data
import matplotlib.pyplot as plt
import altair as alt
import os

st.set_page_config(page_title="MovieGraph", layout="wide")

# Branding styles
st.markdown("""
<style>
    html, body, [class*="css"]  {
        font-family: Verdana;
        color: #2a2a2a;
    }
    .title {
        font-family: 'Courier New', monospace;
        font-weight: normal;
        font-size: 36px;
        margin-bottom: 0;
    }
    .subtitle {
        font-size: 18px;
        letter-spacing: 2px;
        font-weight: bold;
    }
    .subtitle span:nth-child(1) { color: #f27802; }
    .subtitle span:nth-child(2) { color: #2e0854; }
    .subtitle span:nth-child(3) { color: #7786c8; }
    .subtitle span:nth-child(4) { color: #708090; }
    .subtitle span:nth-child(5) { color: #b02711; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">MovieGraph</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle"><span>C</span><span>H</span><span>U</span><span>C</span><span>K</span></div>', unsafe_allow_html=True)

BACKEND_PATH = "data/backend_movie_data.csv"
REQUIRED_COLUMNS = [
    "Title", "Rank", "Year", "Genre", "Director", "Cast",
    "IMDB Rating", "Rotten Tomatoes", "Metacritic Score", "Awards",
    "Runtime", "Language", "Overview",
    "Box Office", "Box Office (Adj)", "Budget", "Budget (Adj)", "Date Added"
]

def load_data():
    if os.path.exists(BACKEND_PATH):
        df = pd.read_csv(BACKEND_PATH)
        st.session_state.movie_data = df
    elif "movie_data" not in st.session_state:
        st.session_state.movie_data = pd.DataFrame(columns=REQUIRED_COLUMNS)
    return st.session_state.movie_data

def save_data(df):
    df.to_csv(BACKEND_PATH, index=False)
    st.session_state.movie_data = df

# (data_management_tab and analytics_tab already defined earlier in the script)

def top_100_tab():
    st.subheader("Top 100 Movies (Upload and Rank)")
    uploaded_file = st.file_uploader("Upload your Top 100 CSV", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        if "Title" not in df.columns and "Movie" in df.columns:
            df.rename(columns={"Movie": "Title"}, inplace=True)
        df = df.dropna(subset=["Title"])
        df["Rank"] = pd.to_numeric(df["Rank"], errors="coerce")
        df["Rank"] = df["Rank"].fillna("").astype(str)

        st.markdown("You can re-order the Top 100 by dragging rows:")
        edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)

        full_df = load_data()
        updated_df = full_df.copy()
        updated_df["Rank"] = ""
        for _, row in edited.iterrows():
            updated_df.loc[updated_df["Title"] == row["Title"], "Rank"] = row["Rank"]
        save_data(updated_df)
        st.success("Top 100 rankings updated!")

# Display all tabs

with st.tabs(["Data Management", "Analytics", "Top 100"]) as (tab1, tab2, tab3):
    with tab1:
        data_management_tab()
    with tab2:
        analytics_tab()
    with tab3:
        top_100_tab()
