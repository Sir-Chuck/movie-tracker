import streamlit as st
import pandas as pd
from datetime import datetime
from tmdb_api import fetch_movie_data
import altair as alt
import os

st.set_page_config(page_title="MovieGraph", layout="wide")

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
        for col in ["Budget", "Box Office", "IMDB Rating", "Rotten Tomatoes", "Metacritic Score"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    return pd.DataFrame(columns=REQUIRED_COLUMNS)

def validate_movie_data(data):
    for col in REQUIRED_COLUMNS:
        if col not in data:
            data[col] = None
    return {k: data.get(k) for k in REQUIRED_COLUMNS}

tabs = st.tabs(["Data Management", "Analytics", "Top 100"])

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

with tabs[1]:
    df = load_data()
    st.subheader("Analytics")

    if df.empty:
        st.info("Add movies to view analytics.")
    else:
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

        # 1. Ratings Distribution
        rating_choice = st.selectbox("Select Rating for Histogram", ["IMDB Rating", "Rotten Tomatoes", "Metacritic Score"])
        st.altair_chart(
            alt.Chart(filtered_df.dropna(subset=[rating_choice])).mark_bar(color=PALETTE[0]).encode(
                x=alt.X(f"{rating_choice}:Q", bin=True),
                y='count()'
            ).properties(title=f"Distribution of {rating_choice}", width=600),
            use_container_width=True
        )

        # 2. Ratings Scatter (colored/sized by Metacritic)
        scatter = alt.Chart(filtered_df.dropna(subset=["IMDB Rating", "Metacritic Score"])).mark_circle().encode(
            x=alt.X("IMDB Rating", scale=alt.Scale(zero=False)),
            y=alt.Y("Metacritic Score", scale=alt.Scale(zero=False)),
            color=alt.Color("Metacritic Score", scale=alt.Scale(scheme='redpurple')),
            size="Metacritic Score",
            tooltip=["Title", "IMDB Rating", "Rotten Tomatoes", "Metacritic Score", "Year", "Director"]
        ).properties(title="IMDB vs Metacritic Ratings", width=600)
        st.altair_chart(scatter, use_container_width=True)

        # 3. Top 10 Summary Tables
        category = st.selectbox("Top 10 By", ["Year", "Genre", "Director", "Cast"])
        def explode_column(df, col):
            return df.dropna(subset=[col]).assign(**{col: df[col].dropna().str.split(",")}).explode(col).dropna(subset=[col])

        top_df = explode_column(filtered_df, category).copy()
        summary = top_df.groupby(category).agg(
            Count=("Title", "count"),
            Avg_IMDB=("IMDB Rating", "mean"),
            Avg_RT=("Rotten Tomatoes", "mean"),
            Avg_Meta=("Metacritic Score", "mean"),
            Avg_Box=("Box Office", "mean"),
            Sum_Box=("Box Office", "sum")
        ).sort_values("Count", ascending=False).head(10).reset_index()
        summary = summary.round({"Avg_IMDB": 2, "Avg_RT": 2, "Avg_Meta": 2, "Avg_Box": 2, "Sum_Box": 2})
        st.dataframe(summary)

        # 4. Grouped Scatter by Selected Category
        group_col = st.selectbox("Bubble Chart Group By", ["Genre", "Year", "Director", "Cast"])
        grouped_df = explode_column(filtered_df, group_col).copy()
        bubble = grouped_df.groupby(group_col).agg(
            Avg_IMDB=("IMDB Rating", "mean"),
            Avg_RT=("Rotten Tomatoes", "mean"),
            Avg_Meta=("Metacritic Score", "mean"),
            Count=("Title", "count")
        ).dropna().reset_index()
        chart = alt.Chart(bubble).mark_circle().encode(
            x=alt.X("Avg_IMDB", title="Avg IMDB Rating"),
            y=alt.Y("Avg_RT", title="Avg Rotten Tomatoes"),
            size="Count",
            color=alt.Color("Avg_Meta", scale=alt.Scale(scheme='redpurple')),
            tooltip=[group_col, "Count", "Avg_IMDB", "Avg_RT", "Avg_Meta"]
        ).properties(title="Grouped Rating Comparison", width=600)
        st.altair_chart(chart, use_container_width=True)

        # 5. Box Office vs Budget
        scatter2 = alt.Chart(filtered_df.dropna(subset=["Budget", "Box Office", "IMDB Rating", "Rotten Tomatoes"])).mark_circle().encode(
            x=alt.X("Budget", title="Budget ($)", axis=alt.Axis(format="$,.2f")),
            y=alt.Y("Box Office", title="Box Office ($)", axis=alt.Axis(format="$,.2f")),
            size="Rotten Tomatoes",
            color=alt.Color("IMDB Rating", scale=alt.Scale(scheme="redpurple")),
            tooltip=["Title", "Budget", "Box Office", "IMDB Rating", "Rotten Tomatoes"]
        ).properties(title="Budget vs Box Office", width=600)
        st.altair_chart(scatter2, use_container_width=True)

        # 6. Dual Axis by Year
        rating_metric = st.selectbox("Metric for Average Rating", ["IMDB Rating", "Rotten Tomatoes", "Metacritic Score"])
        yearly = filtered_df.groupby("Year").agg(
            Movie_Count=("Title", "count"),
            Avg_Rating=(rating_metric, "mean")
        ).dropna().reset_index()

        base = alt.Chart(yearly).encode(x=alt.X("Year:O", axis=alt.Axis(format="d")))
        bars = base.mark_bar(color=PALETTE[0]).encode(y=alt.Y("Movie_Count", axis=alt.Axis(title="Count")))
        line = base.mark_line(color=PALETTE[2]).encode(y=alt.Y("Avg_Rating", axis=alt.Axis(title=f"Avg {rating_metric}")))
        st.altair_chart((bars + line).resolve_scale(y="independent").properties(title="Movies Over Time"), use_container_width=True)

with tabs[2]:
    def top_100_tab():
        st.subheader("Top 100")
        st.info("Top 100 movie ranking functionality will be added here.")
    top_100_tab()
