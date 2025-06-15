# app.py
import streamlit as st
import pandas as pd
from datetime import datetime
from tmdb_api import fetch_movie_data
from analytics_tab import analytics_tab
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
        return pd.read_csv(BACKEND_PATH)
    return pd.DataFrame(columns=REQUIRED_COLUMNS)

def save_data(df):
    os.makedirs(os.path.dirname(BACKEND_PATH), exist_ok=True)
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

    # === Filters reused from Analytics ===
    st.subheader("🔍 Filter Your Movie Collection")

    def parse_list_column(col):
        return col.apply(lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith("[") else [])

    df["Genre"] = parse_list_column(df.get("Genre", pd.Series([])))
    df["Cast"] = parse_list_column(df.get("Cast", pd.Series([])))
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Budget"] = pd.to_numeric(df["Budget"].astype(str).str.replace("[$,]", "", regex=True), errors="coerce")
    df["Box Office"] = pd.to_numeric(df["Box Office"].astype(str).str.replace("[$,]", "", regex=True), errors="coerce")

    all_genres = sorted({g for genres in df["Genre"].dropna() for g in genres})
    all_cast = sorted({c for cast in df["Cast"].dropna() for c in cast})
    all_directors = sorted(df["Director"].dropna().unique())

    col1, col2, col3 = st.columns(3)
    with col1:
        year_range = st.slider("Year", int(df["Year"].min()), int(df["Year"].max()), (int(df["Year"].min()), int(df["Year"].max())))
        genre_filter = st.multiselect("Genres", all_genres)
    with col2:
        budget_range = st.slider("Budget ($)", int(df["Budget"].min()), int(df["Budget"].max()), (int(df["Budget"].min()), int(df["Budget"].max())))
        box_office_range = st.slider("Box Office ($)", int(df["Box Office"].min()), int(df["Box Office"].max()), (int(df["Box Office"].min()), int(df["Box Office"].max())))
    with col3:
        director_filter = st.multiselect("Directors", all_directors)
        actor_filter = st.multiselect("Actors", all_cast)

    def matches(row):
        return (
            year_range[0] <= row["Year"] <= year_range[1]
            and budget_range[0] <= row["Budget"] <= budget_range[1]
            and box_office_range[0] <= row["Box Office"] <= box_office_range[1]
            and (not genre_filter or any(g in row["Genre"] for g in genre_filter))
            and (not director_filter or row["Director"] in director_filter)
            and (not actor_filter or any(a in row["Cast"] for a in actor_filter))
        )

    filtered_df = df[df.apply(matches, axis=1)].copy()

    st.subheader("Your Movie Collection")
    st.write(f"Total Movies: {len(filtered_df)}")
    st.dataframe(filtered_df.sort_values("Date Added", ascending=False), use_container_width=True)

    return df

tabs = st.tabs(["Data Management", "Analytics", "Top 100"])

with tabs[0]:
    df = data_management_tab()

with tabs[1]:
    analytics_tab(df, show_filters=True)

with tabs[2]:
    st.subheader("Top 100")
    st.info("Top 100 movie ranking functionality will be added here.")
