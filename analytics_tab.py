# analytics_tab.py
import streamlit as st
import pandas as pd
import altair as alt

def analytics_tab(df):
    st.subheader("Analytics")

    # --- Data Cleaning ---
    df["Box Office"] = pd.to_numeric(df["Box Office"].str.replace("[$,]", "", regex=True), errors="coerce")
    df["Budget"] = pd.to_numeric(df["Budget"].str.replace("[$,]", "", regex=True), errors="coerce")

    df["IMDB Rating"] = pd.to_numeric(df["IMDB Rating"], errors="coerce")
    df["Metacritic Score"] = pd.to_numeric(df["Metacritic Score"], errors="coerce")
    df["Rotten Percent"] = df["Rotten Tomatoes"].str.replace("%", "").astype(float)

    # Genre and Cast from list to exploded rows
    df["Genre"] = df["Genre"].apply(lambda x: eval(x) if isinstance(x, str) else x)
    df["Cast"] = df["Cast"].apply(lambda x: eval(x) if isinstance(x, str) else x)
    df = df.explode("Genre")
    df = df.explode("Cast")

    # --- Sidebar Filters (only visible in this tab) ---
    st.sidebar.header("🔍 Filter Options")
    year_range = st.sidebar.slider("Year Range", int(df["Year"].min()), int(df["Year"].max()), (2000, 2025))
    selected_genres = st.sidebar.multiselect("Genres", sorted(df["Genre"].dropna().unique()))
    selected_director = st.sidebar.multiselect("Director", sorted(df["Director"].dropna().unique()))
    selected_actor = st.sidebar.multiselect("Actor", sorted(df["Cast"].dropna().unique()))

    filtered_df = df[
        (df["Year"].between(*year_range)) &
        (df["Genre"].isin(selected_genres) if selected_genres else True) &
        (df["Director"].isin(selected_director) if selected_director else True) &
        (df["Cast"].isin(selected_actor) if selected_actor else True)
    ]

    # --- Ratings Histogram ---
    st.markdown("### 🎯 Ratings Distribution")
    rating_type = st.selectbox("Choose Rating Type", ["IMDB Rating", "Rotten Percent", "Metacritic Score"])
    hist = alt.Chart(filtered_df).mark_bar().encode(
        alt.X(f"{rating_type}:Q", bin=True),
        y='count()',
        tooltip=[rating_type, "Title"]
    ).properties(width=700, height=300).configure_mark(opacity=0.85, color="#2e0854")
    st.altair_chart(hist, use_container_width=True)

    # --- Ratings Scatter ---
    st.markdown("### 🎬 Ratings Scatter Plot (IMDB vs Rotten Tomatoes)")
    scatter = alt.Chart(filtered_df).mark_circle().encode(
        x="IMDB Rating:Q",
        y="Rotten Percent:Q",
        size="Metacritic Score:Q",
        color="Metacritic Score:Q",
        tooltip=["Title", "IMDB Rating", "Rotten Percent", "Metacritic Score", "Year", "Director"]
    ).interactive().properties(width=700, height=400)
    st.altair_chart(scatter, use_container_width=True)

    # --- Top 10 Summary Table ---
    st.markdown("### 📊 Top 10 Summary")
    group_by = st.selectbox("Group By", ["Genre", "Cast", "Director", "Year"])
    summary = filtered_df.groupby(group_by).agg({
        "Title": "count",
        "IMDB Rating": "mean",
        "Rotten Percent": "mean",
        "Metacritic Score": "mean",
        "Box Office": "sum"
    }).rename(columns={"Title": "Movie Count"}).sort_values("Movie Count", ascending=False).head(10)
    summary["IMDB Rating"] = summary["IMDB Rating"].round(2)
    summary["Rotten Percent"] = summary["Rotten Percent"].round(2)
    summary["Metacritic Score"] = summary["Metacritic Score"].round(2)
    summary["Box Office"] = summary["Box Office"].apply(lambda x: f"${x:,.2f}")
    st.dataframe(summary)

    # Placeholder for future charts like dual-axis or category scatterplots
