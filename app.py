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
    df_display = df.copy()
    df_display["Top 100"] = df_display["Rank"].apply(lambda x: int(x) if pd.notna(x) and str(x).isdigit() else "")
    st.dataframe(df_display[REQUIRED_COLUMNS + ["Top 100"]], use_container_width=True)

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

    filter_top_100 = st.checkbox("Only show Top 100")
    if filter_top_100:
        df = df[pd.to_numeric(df["Rank"], errors="coerce").notna()]

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

# Remaining top_100_tab() and tabs setup unchanged
