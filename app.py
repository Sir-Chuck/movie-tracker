import streamlit as st
import pandas as pd
from datetime import datetime
from tmdb_api import fetch_movie_data
import os

st.set_page_config(page_title="MovieGraph", layout="wide")

# --- Branding ---
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

# --- Paths & Columns ---
BACKEND_PATH = "data/backend_movie_data.csv"
REQUIRED_COLUMNS = [
    "Title", "Rank", "Year", "Genre", "Director", "Cast",
    "IMDB Rating", "Rotten Tomatoes", "Metacritic Score", "Awards",
    "Runtime", "Language", "Overview",
    "Box Office", "Box Office (Adj)", "Budget", "Budget (Adj)", "Date Added"
]

# --- Utility Functions ---
def load_data():
    if os.path.exists(BACKEND_PATH):
        return pd.read_csv(BACKEND_PATH)
    return pd.DataFrame(columns=REQUIRED_COLUMNS)

def validate_movie_data(data):
    """Ensure all required columns are present and consistently ordered."""
    for col in REQUIRED_COLUMNS:
        if col not in data:
            data[col] = None
    return {k: data.get(k) for k in REQUIRED_COLUMNS}

# --- UI Tabs ---
tabs = st.tabs(["Data Management", "Analytics", "Top 100"])

# --- Data Management Tab ---
with tabs[0]:
    st.subheader("Add Movies to Your Collection")
    title_input = st.text_area("Enter movie titles (one per line):")
    if st.button("Add Movies"):
        if title_input.strip():
            movie_titles = [title.strip() for title in title_input.strip().split("\n") if title.strip()]
            existing_df = load_data()
            with st.spinner("Fetching movie data..."):
                new_movies, skipped, not_found = [], [], []
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
                    st.progress((i + 1) / len(movie_titles))
            if new_movies:
                df_new = pd.DataFrame(new_movies)
                df_new["Date Added"] = datetime.now().strftime("%Y-%m-%d")
                updated_df = pd.concat([existing_df, df_new], ignore_index=True)
                updated_df.to_csv(BACKEND_PATH, index=False)
                st.success(f"✅ Added: {len(new_movies)} movies")
                if skipped:
                    st.warning(f"⚠️ Skipped (already in collection): {', '.join(skipped)}")
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
    def analytics_tab():
        st.subheader("Analytics")
        st.info("Analytics functionality will be added here.")
    analytics_tab()

# --- Top 100 Tab ---
with tabs[2]:
    def top_100_tab():
        st.subheader("Top 100")
        st.info("Top 100 movie ranking functionality will be added here.")
    top_100_tab()
