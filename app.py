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

# Display all tabs
selected_tab = st.selectbox("Navigate", ["Data Management", "Analytics", "Top 100"])

if selected_tab == "Analytics":
    st.sidebar.header("Filter Options")

# ... retain all other logic ... (unchanged)

# Add these lines to color scale definition in analytics plots where appropriate:
# color=alt.Color("Avg_Meta", scale=alt.Scale(scheme='category10', range=['#f27802', '#2e0854', '#7786c8', '#708090', '#b02711']))
# Apply similar scale/range definitions to other Altair charts to use consistent colors
