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

def data_management_tab():
    df = load_data()
    st.subheader("Add Movies to Your Collection")

    titles = st.text_area("Enter movie titles (one per line):")
    if st.button("Add Movies"):
        titles_list = [t.strip() for t in titles.split("\n") if t.strip()]
        added, skipped, not_found = [], [], []
        progress = st.progress(0)

        with st.spinner("Fetching movie data..."):
            for i, title in enumerate(titles_list):
                progress.progress((i + 1) / len(titles_list))
                if title in df["Title"].values:
                    skipped.append(title)
                    continue
                movie = fetch_movie_data(title)
                if movie:
                    movie["Date Added"] = datetime.now().strftime("%Y-%m-%d")
                    movie["Rank"] = ""
                    df = pd.concat([df, pd.DataFrame([movie])], ignore_index=True)
                    added.append(title)
                else:
                    not_found.append(title)

        save_data(df)
        st.success(f"✅ Added: {len(added)} | ⏩ Skipped: {len(skipped)} | ❌ Not Found: {len(not_found)}")
        if skipped:
            st.info("Skipped Movies: " + ", ".join(skipped))
        if not_found:
            st.warning("Not Found: " + ", ".join(not_found))

    st.subheader("Your Movie Collection")
    st.markdown(f"**Total Movies:** {len(df)}")
    st.dataframe(df[REQUIRED_COLUMNS], use_container_width=True)

    if st.button("Clear Data"):
        st.session_state.movie_data = pd.DataFrame(columns=REQUIRED_COLUMNS)
        if os.path.exists(BACKEND_PATH):
            os.remove(BACKEND_PATH)
        st.success("All movie data cleared.")
        st.experimental_rerun()

def analytics_tab():
    df = load_data()
    if df.empty:
        st.info("No data to analyze. Add movies first.")
        return

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["IMDB Rating"] = pd.to_numeric(df["IMDB Rating"], errors="coerce")
    df["Metacritic Score"] = pd.to_numeric(df["Metacritic Score"], errors="coerce")
    df["Box Office (Adj)"] = pd.to_numeric(df["Box Office (Adj)"], errors="coerce")
    df["Budget (Adj)"] = pd.to_numeric(df["Budget (Adj)"], errors="coerce")
    df["Rotten Percent"] = pd.to_numeric(df["Rotten Tomatoes"].str.replace("%", "", regex=False), errors="coerce")

    st.subheader("Interactive Analytics")

    st.markdown("### 🎬 Movie Count by Genre")
    genre_counts = df["Genre"].str.split(", ").explode().value_counts().reset_index()
    genre_counts.columns = ["Genre", "Count"]
    bar_genre = alt.Chart(genre_counts).mark_bar(color="#f27802").encode(
        x="Count:Q", y=alt.Y("Genre:N", sort="-x")
    )
    st.altair_chart(bar_genre, use_container_width=True)

    st.markdown("### 📊 IMDB vs Metacritic vs Rotten Tomatoes")
    scatter = alt.Chart(df.dropna(subset=["IMDB Rating", "Metacritic Score", "Rotten Percent"])).mark_circle(size=80).encode(
        x="IMDB Rating",
        y="Metacritic Score",
        size="Rotten Percent",
        color="Genre:N",
        tooltip=["Title", "Director", "IMDB Rating", "Metacritic Score", "Rotten Percent"]
    ).interactive()
    st.altair_chart(scatter, use_container_width=True)

    st.markdown("### 📈 Average Ratings by Year")
    ratings_by_year = df.groupby("Year")[["IMDB Rating", "Metacritic Score"]].mean().reset_index()
    line = alt.Chart(ratings_by_year).transform_fold(
        ["IMDB Rating", "Metacritic Score"], as_=["Source", "Rating"]
    ).mark_line().encode(
        x="Year:O",
        y="Rating:Q",
        color="Source:N"
    )
    st.altair_chart(line, use_container_width=True)

    st.markdown("### 💰 Box Office vs Budget (Bubble Size = IMDB Rating)")
    bubble = alt.Chart(df.dropna(subset=["Box Office (Adj)", "Budget (Adj)", "IMDB Rating"])).mark_circle().encode(
        x="Budget (Adj)",
        y="Box Office (Adj)",
        size="IMDB Rating",
        color="Genre:N",
        tooltip=["Title", "Box Office (Adj)", "Budget (Adj)", "IMDB Rating"]
    ).interactive()
    st.altair_chart(bubble, use_container_width=True)

def top_100_tab():
    st.subheader("📥 Upload Your Top 100 Ranked Movies")
    uploaded_file = st.file_uploader("Upload CSV file with columns: Title (or Movie), Rank", type="csv")

    if uploaded_file:
        with st.spinner("Loading CSV file..."):
            rank_df = pd.read_csv(uploaded_file)

        rank_df.columns = rank_df.columns.str.strip().str.lower()
        title_col = "title" if "title" in rank_df.columns else "movie"
        rank_df = rank_df.rename(columns={title_col: "Title", "rank": "Rank"})
        rank_df = rank_df.dropna(subset=["Title", "Rank"])
        collection = load_data()

        added_movies = []
        progress = st.progress(0)

        for i, (_, row) in enumerate(rank_df.iterrows()):
            progress.progress((i + 1) / len(rank_df))
            title = row["Title"].strip()
            if title in collection["Title"].values:
                continue
            movie = fetch_movie_data(title)
            if movie:
                movie["Date Added"] = datetime.now().strftime("%Y-%m-%d")
                movie["Rank"] = row["Rank"]
                added_movies.append(movie)

        if added_movies:
            combined = pd.DataFrame(added_movies)
            collection = pd.concat([collection, combined], ignore_index=True)
            save_data(collection)
            st.success(f"🎉 Added {len(added_movies)} ranked movies!")

        st.markdown("### 🏆 Top 100 Ranked List")
        full = collection[collection["Title"].isin(rank_df["Title"])].copy()
        full["Rank"] = pd.to_numeric(full["Rank"], errors="coerce")
        st.dataframe(full.sort_values("Rank")[["Rank", "Title"] + [col for col in REQUIRED_COLUMNS if col not in ["Title", "Rank"]]], use_container_width=True)

# Tabs
tabs = st.tabs(["Data Management", "Analytics", "Top 100"])

with tabs[0]:
    data_management_tab()
with tabs[1]:
    analytics_tab()
with tabs[2]:
    top_100_tab()
