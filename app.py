# app.py
import os
import pandas as pd
import streamlit as st
from datetime import datetime
from tmdb_api import fetch_movie_data
import matplotlib.pyplot as plt
import seaborn as sns

DATA_FILE = "movies.csv"
REQUIRED_COLUMNS = [
    "Title", "Year", "Genre", "Director", "Cast", "IMDB Rating",
    "Runtime", "Language", "Overview", "Date Added"
]

# Style
st.markdown("""
    <style>
        html, body, [class*="css"]  {
            font-family: Verdana;
            color: #2a2a2a;
        }
        .title-font {
            font-family: 'Courier New', monospace;
            font-weight: normal;
            font-size: 36px;
        }
        .chuck {
            font-size: 24px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class='title-font'>MovieGraph</div>
    <div class='chuck'>
        <span style='color:#f27802'>C</span><span style='color:#2e0854'>H</span><span style='color:#7786c8'>U</span><span style='color:#708090'>C</span><span style='color:#b02711'>K</span>
    </div>
""", unsafe_allow_html=True)

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[REQUIRED_COLUMNS]

def is_duplicate(entry, df):
    title = entry.get("Title", "").strip().lower()
    year = str(entry.get("Year", "")).strip()

    if df.empty:
        return False

    df_check = df.copy()
    df_check["Title"] = df_check["Title"].astype(str).str.strip().str.lower()
    df_check["Year"] = df_check["Year"].astype(str).str.strip()

    return ((df_check["Title"] == title) & (df_check["Year"] == year)).any()

def add_movies(titles, df):
    added, skipped, failed = [], [], []
    progress = st.progress(0, text="⏳ Fetching movies...")

    total = len(titles)
    for i, title in enumerate(titles):
        progress.progress((i + 1) / total, text=f"Fetching: {title} ({i+1}/{total})")

        movie = fetch_movie_data(title)
        if not movie:
            failed.append(title)
            continue

        movie["Date Added"] = datetime.today().strftime("%Y-%m-%d")
        for col in REQUIRED_COLUMNS:
            movie.setdefault(col, "")

        if not is_duplicate(movie, df):
            df = pd.concat([df, pd.DataFrame([movie])], ignore_index=True)
            added.append(title)
        else:
            skipped.append(title)

    progress.empty()
    return df, added, skipped, failed

def show_data_management(df):
    st.header("📥 Add Movies (Batch)")
    titles_input = st.text_area("Enter one movie title per line:")
    if st.button("Add Movies"):
        titles = [t.strip() for t in titles_input.splitlines() if t.strip()]
        if titles:
            df, added, skipped, failed = add_movies(titles, df)
            df.to_csv(DATA_FILE, index=False)

            st.success(f"✅ Added: {len(added)} movies")
            if skipped:
                st.info(f"⏭️ Skipped (already in collection): {len(skipped)}")
            if failed:
                st.error(f"❌ Not found in TMDb: {len(failed)}")

    st.header("➕ Add Single Movie")
    title_single = st.text_input("Movie title:")
    if st.button("Add This Movie"):
        if title_single.strip():
            df, added, skipped, failed = add_movies([title_single.strip()], df)
            df.to_csv(DATA_FILE, index=False)

            if added:
                st.success(f"✅ Added: {title_single}")
            elif skipped:
                st.info("⏭️ Skipped: already in collection")
            elif failed:
                st.error("❌ Could not find that movie")

    st.header("🧼 Data Management")
    if "data_cleared" not in st.session_state:
        st.session_state["data_cleared"] = False

    if st.button("❌ Clear All Movie Data"):
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)
        df.to_csv(DATA_FILE, index=False)
        st.session_state["data_cleared"] = True
        st.success("All movie data has been cleared. Reloading...")

    if st.session_state["data_cleared"]:
        st.session_state["data_cleared"] = False
        st.stop()

    st.header("🎯 Your Movie Collection")
    st.dataframe(df, use_container_width=True)

def show_analytics(df):
    st.header("📊 Movie Collection Analytics")

    if df.empty:
        st.warning("No data to analyze. Add movies first.")
        return

    df["IMDB Rating"] = pd.to_numeric(df["IMDB Rating"], errors="coerce")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")

    st.subheader("🎬 By Release Year")
    year_summary = df.groupby("Year")["Title"].count().reset_index(name="Movie Count")
    st.dataframe(year_summary)
    fig, ax = plt.subplots()
    sns.histplot(df["Year"].dropna(), bins=20, color="#f27802", ax=ax)
    ax.set_title("Distribution of Release Years")
    st.pyplot(fig)

    st.subheader("🎥 By Director")
    dir_summary = df.groupby("Director").agg({"Title": "count", "IMDB Rating": "mean"}).reset_index()
    st.dataframe(dir_summary.sort_values("Title", ascending=False).head(10))

    st.subheader("📚 By Genre")
    genre_counts = df["Genre"].str.split(", ").explode().value_counts().reset_index()
    genre_counts.columns = ["Genre", "Count"]
    st.dataframe(genre_counts.head(10))
    fig, ax = plt.subplots()
    sns.barplot(data=genre_counts.head(10), x="Count", y="Genre", palette=["#2e0854"]*10, ax=ax)
    ax.set_title("Top Genres")
    st.pyplot(fig)

    st.subheader("⭐ By Actor")
    actor_counts = df["Cast"].str.split(", ").explode().value_counts().reset_index()
    actor_counts.columns = ["Actor", "Count"]
    st.dataframe(actor_counts.head(10))
    fig, ax = plt.subplots()
    sns.barplot(data=actor_counts.head(10), x="Count", y="Actor", palette=["#7786c8"]*10, ax=ax)
    ax.set_title("Most Frequent Actors")
    st.pyplot(fig)

def main():
    df = load_data()
    tab1, tab2 = st.tabs(["Data Management", "Analytics"])

    with tab1:
        show_data_management(df)

    with tab2:
        show_analytics(df)

if __name__ == "__main__":
    main()
