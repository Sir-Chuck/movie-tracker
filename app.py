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
    st.subheader("Add Movies")
    df = load_data()
    movie_input = st.text_area("Enter movie titles (one per line):")
    if st.button("Add Movies"):
        new_titles = [m.strip() for m in movie_input.split("\n") if m.strip()]
        existing_titles = df["Title"].str.lower().tolist()
        added, skipped, not_found = [], [], []

        progress = st.progress(0)
        for i, title in enumerate(new_titles):
            progress.progress((i + 1) / len(new_titles))
            if title.lower() in existing_titles:
                skipped.append(title)
                continue
            data = fetch_movie_data(title)
            if data:
                data["Date Added"] = datetime.now().strftime("%Y-%m-%d")
                df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
                added.append(title)
            else:
                not_found.append(title)

        save_data(df)
        st.success(f"✅ Added: {len(added)}, Skipped: {len(skipped)}, Not Found: {len(not_found)}")
        if skipped:
            st.info("Skipped: " + ", ".join(skipped))
        if not_found:
            st.warning("Not Found: " + ", ".join(not_found))

    if st.button("Clear All Data"):
        st.session_state.movie_data = pd.DataFrame(columns=REQUIRED_COLUMNS)
        save_data(st.session_state.movie_data)
        st.success("All movie data cleared.")

    st.subheader("Your Movie Collection")
    df = load_data()
    st.write(f"Total Movies: {len(df)}")
    st.dataframe(df[REQUIRED_COLUMNS], use_container_width=True)

def analytics_tab():
    st.subheader("Analytics Dashboard")
    df = load_data()
    if df.empty:
        st.info("No data to analyze. Add movies first.")
        return

    # Filtering options
    st.sidebar.header("Filter Options")
    year_range = st.sidebar.slider("Year Range", int(df["Year"].min()), int(df["Year"].max()), (int(df["Year"].min()), int(df["Year"].max())))
    genres = st.sidebar.multiselect("Genres", sorted(set(g for sub in df["Genre"].dropna().str.split(", ") for g in sub)))
    directors = st.sidebar.multiselect("Directors", sorted(df["Director"].dropna().unique()))
    actors = st.sidebar.multiselect("Actors", sorted(set(a for sub in df["Cast"].dropna().str.split(", ") for a in sub)))
    min_budget, max_budget = st.sidebar.slider("Budget Range", 0, int(df["Budget"].max()), (0, int(df["Budget"].max())))
    min_box, max_box = st.sidebar.slider("Box Office Range", 0, int(df["Box Office"].max()), (0, int(df["Box Office"].max())))

    df = df[(df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1])]
    if genres:
        df = df[df["Genre"].apply(lambda g: any(genre in g for genre in genres) if pd.notnull(g) else False)]
    if directors:
        df = df[df["Director"].isin(directors)]
    if actors:
        df = df[df["Cast"].apply(lambda c: any(actor in c for actor in actors) if pd.notnull(c) else False)]
    df = df[(df["Budget"] >= min_budget) & (df["Budget"] <= max_budget)]
    df = df[(df["Box Office"] >= min_box) & (df["Box Office"] <= max_box)]

    df["IMDB Rating"] = pd.to_numeric(df["IMDB Rating"], errors="coerce")
    df["Metacritic Score"] = pd.to_numeric(df["Metacritic Score"], errors="coerce")
    df["Rotten Percent"] = pd.to_numeric(df["Rotten Tomatoes"].str.replace("%", "", regex=False), errors="coerce")

    if st.checkbox("Show only Top 100"):
        df = df[df["Rank"].notna() & (df["Rank"] != "")]

    # Histogram
    rating_type = st.selectbox("Rating Type for Histogram", ["IMDB Rating", "Rotten Percent", "Metacritic Score"])
    st.markdown("### Ratings Distribution")
    st.bar_chart(df[rating_type].dropna().value_counts().sort_index())

    # Ratings scatter
    st.markdown("### Ratings Scatter: IMDB vs Rotten Tomatoes")
    scatter = alt.Chart(df).mark_circle().encode(
        x='IMDB Rating',
        y='Rotten Percent',
        color='Metacritic Score',
        size='Metacritic Score',
        tooltip=['Title', 'IMDB Rating', 'Rotten Percent', 'Metacritic Score', 'Year', 'Director']
    ).interactive()
    st.altair_chart(scatter, use_container_width=True)

    # Top 10 tables
    for category in ["Year", "Genre", "Cast", "Director"]:
        st.markdown(f"### Top 10 by {category}")
        exploded = df.copy()
        if category in ["Genre", "Cast"]:
            exploded = exploded.dropna(subset=[category])
            exploded = exploded.assign(**{category: exploded[category].str.split(", ")}).explode(category)
        summary = exploded.groupby(category).agg(
            Count=("Title", "count"),
            Avg_IMDB=("IMDB Rating", "mean"),
            Avg_RT=("Rotten Percent", "mean"),
            Avg_Meta=("Metacritic Score", "mean"),
            Avg_Box=("Box Office", "mean"),
            Total_Box=("Box Office", "sum")
        ).sort_values("Count", ascending=False).head(10).reset_index()
        st.dataframe(summary, use_container_width=True)

    # Bubble chart by category
    st.markdown("### Average Ratings by Category")
    bubble_dim = st.selectbox("Group By", ["Genre", "Year", "Cast", "Director"])
    bubble_df = df.copy()
    if bubble_dim in ["Genre", "Cast"]:
        bubble_df = bubble_df.dropna(subset=[bubble_dim])
        bubble_df = bubble_df.assign(**{bubble_dim: bubble_df[bubble_dim].str.split(", ")}).explode(bubble_dim)
    grouped = bubble_df.groupby(bubble_dim).agg(
        Count=("Title", "count"),
        Avg_IMDB=("IMDB Rating", "mean"),
        Avg_RT=("Rotten Percent", "mean"),
        Avg_Meta=("Metacritic Score", "mean")
    ).reset_index()
    bubble = alt.Chart(grouped).mark_circle().encode(
        x="Avg_IMDB",
        y="Avg_RT",
        size="Count",
        color="Avg_Meta",
        tooltip=[bubble_dim, "Count", "Avg_IMDB", "Avg_RT", "Avg_Meta"]
    ).interactive()
    st.altair_chart(bubble, use_container_width=True)

    # Scatter for box office vs budget
    st.markdown("### Box Office vs Budget")
    bo_scatter = alt.Chart(df).mark_circle().encode(
        x="Budget",
        y="Box Office",
        color="IMDB Rating",
        size="Rotten Percent",
        tooltip=["Title", "Box Office", "Budget", "IMDB Rating"]
    ).interactive()
    st.altair_chart(bo_scatter, use_container_width=True)

    # Dual-axis chart
    st.markdown("### Movies Over Time")
    rating_y = st.selectbox("Select rating for Y axis", ["IMDB Rating", "Rotten Percent", "Metacritic Score"])
    yearly = df.groupby("Year").agg(
        Count=("Title", "count"),
        Avg_Rating=(rating_y, "mean")
    ).reset_index()
    bars = alt.Chart(yearly).mark_bar().encode(x="Year", y="Count")
    line = alt.Chart(yearly).mark_line(color="#f27802").encode(x="Year", y="Avg_Rating")
    st.altair_chart(bars + line, use_container_width=True)

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

tabs = st.tabs(["Data Management", "Analytics", "Top 100"])
with tabs[0]:
    data_management_tab()
with tabs[1]:
    analytics_tab()
with tabs[2]:
    top_100_tab()
