import streamlit as st
import pandas as pd
from datetime import datetime
from tmdb_api import fetch_movie_data
import altair as alt
import os

st.set_page_config(page_title="MovieGraph", layout="wide")

# --- Styling ---
PALETTE = ['#f27802', '#2e0854', '#7786c8', '#708090', '#b02711']

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

# --- Setup ---
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
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce").fillna(0).astype(int)
        df["Budget"] = pd.to_numeric(df["Budget"], errors="coerce")
        df["Box Office"] = pd.to_numeric(df["Box Office"], errors="coerce")
        df["IMDB Rating"] = pd.to_numeric(df["IMDB Rating"], errors="coerce")
        df["Rotten Tomatoes"] = pd.to_numeric(df["Rotten Tomatoes"], errors="coerce")
        df["Metacritic Score"] = pd.to_numeric(df["Metacritic Score"], errors="coerce")
        return df
    return pd.DataFrame(columns=REQUIRED_COLUMNS)

def validate_movie_data(data):
    for col in REQUIRED_COLUMNS:
        if col not in data:
            data[col] = None
    return {k: data.get(k) for k in REQUIRED_COLUMNS}

# --- Tabs ---
tabs = st.tabs(["Data Management", "Analytics", "Top 100"])

# --- Data Management ---
with tabs[0]:
    st.subheader("Add Movies to Your Collection")
    title_input = st.text_area("Enter movie titles (one per line):")
    if st.button("Add Movies"):
        if title_input.strip():
            movie_titles = [title.strip() for title in title_input.strip().split("\n") if title.strip()]
            existing_df = load_data()
            with st.spinner("Fetching movie data..."):
                new_movies, skipped, not_found = [], [], []
                progress_bar = st.progress(0)
                for i, title in enumerate(movie_titles):
                    if title in existing_df["Title"].values:
                        skipped.append(title)
                        continue
                    data = fetch_movie_data(title)
                    if data:
                        validated = validate_movie_data(data)
                        new_movies.append(validated)
                    else:
                        not_found.append(title)
                    progress_bar.progress((i + 1) / len(movie_titles))
                if new_movies:
                    df_new = pd.DataFrame(new_movies)
                    df_new["Date Added"] = datetime.now().strftime("%Y-%m-%d")
                    updated_df = pd.concat([existing_df, df_new], ignore_index=True)
                    updated_df.to_csv(BACKEND_PATH, index=False)
                    st.success(f"✅ Added: {len(new_movies)} movies")
                    if skipped:
                        st.warning(f"⚠️ Skipped: {', '.join(skipped)}")
                    if not_found:
                        st.error(f"❌ Not found: {', '.join(not_found)}")
                else:
                    st.info("No new movies were added.")

    df = load_data()
    st.subheader("Your Movie Collection")
    if df.empty:
        st.info("No movies in your collection yet.")
    else:
        st.write(f"Total Movies: {len(df)}")
        st.dataframe(df.sort_values("Date Added", ascending=False), use_container_width=True)

# --- Analytics Tab ---
with tabs[1]:
    df = load_data()
    st.subheader("Analytics")

    if df.empty:
        st.info("Add movies to view analytics.")
    else:
        # --- Sidebar Filters ---
        with st.sidebar:
            st.markdown("### Filters")
            years = df["Year"].dropna()
            year_range = st.slider("Year", int(years.min()), int(years.max()), (int(years.min()), int(years.max())))
            genres = sorted(set(g.strip() for sublist in df["Genre"].dropna().str.split(",") for g in sublist))
            selected_genres = st.multiselect("Genre", genres, default=genres)
            budget_range = st.slider("Budget ($)", 0, int(df["Budget"].max()), (0, int(df["Budget"].max())))
            box_range = st.slider("Box Office ($)", 0, int(df["Box Office"].max()), (0, int(df["Box Office"].max())))
            directors = sorted(df["Director"].dropna().unique())
            selected_director = st.selectbox("Director", ["All"] + directors)
            actors = sorted(set(actor.strip() for sublist in df["Cast"].dropna().str.split(",") for actor in sublist))
            selected_actor = st.selectbox("Actor", ["All"] + actors)

        # --- Apply Filters ---
        def movie_has_selected_genre(genre_string):
            if pd.isna(genre_string):
                return False
            movie_genres = [g.strip() for g in genre_string.split(",")]
            return any(g in selected_genres for g in movie_genres)

        filtered_df = df[
            (df["Year"].between(*year_range)) &
            (df["Budget"].between(*budget_range)) &
            (df["Box Office"].between(*box_range)) &
            df["Genre"].apply(movie_has_selected_genre)
        ]
        if selected_director != "All":
            filtered_df = filtered_df[filtered_df["Director"] == selected_director]
        if selected_actor != "All":
            filtered_df = filtered_df[filtered_df["Cast"].str.contains(selected_actor, na=False)]

        # --- Visualizations ---
        from analytics_tab import render_analytics_tab
        render_analytics_tab(filtered_df, palette=PALETTE)

# --- Top 100 Tab ---
with tabs[2]:
    def top_100_tab():
        st.subheader("Top 100")
        st.info("Top 100 movie ranking functionality will be added here.")
    top_100_tab()
