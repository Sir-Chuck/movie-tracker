import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
import ast

# Color palette
PALETTE = ['#f27802', '#2e0854', '#7786c8', '#708090', '#b02711']

def safe_parse_list(val):
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            return ast.literal_eval(val)
        except (ValueError, SyntaxError):
            return [v.strip() for v in val.split(',')]
    return []

def analytics_tab(df):
    # Preprocessing
    df["Box Office"] = pd.to_numeric(df["Box Office"].astype(str).str.replace("[$,]", "", regex=True), errors="coerce")
    df["Budget"] = pd.to_numeric(df["Budget"].astype(str).str.replace("[$,]", "", regex=True), errors="coerce")
    df["IMDB Rating"] = pd.to_numeric(df["IMDB Rating"], errors="coerce")
    df["Metacritic Score"] = pd.to_numeric(df["Metacritic Score"], errors="coerce")
    df["Rotten Percent"] = df["Rotten Tomatoes"].astype(str).str.replace("%", "").astype(float)

    df["Genre"] = df["Genre"].apply(safe_parse_list)
    df["Cast"] = df["Cast"].apply(safe_parse_list)

    genre_exploded = df.explode("Genre")
    cast_exploded = df.explode("Cast")

    with st.sidebar:
        st.markdown("### 🎯 Filters")
        year_range = st.slider("Year", int(df["Year"].min()), int(df["Year"].max()), (int(df["Year"].min()), int(df["Year"].max())))
        genres = st.multiselect("Genre", options=genre_exploded["Genre"].dropna().unique())
        directors = st.multiselect("Director", options=df["Director"].dropna().unique())
        actors = st.multiselect("Actor", options=cast_exploded["Cast"].dropna().unique())
        box_range = st.slider("Box Office ($)", float(df["Box Office"].min()), float(df["Box Office"].max()), (float(df["Box Office"].min()), float(df["Box Office"].max())))
        budget_range = st.slider("Budget ($)", float(df["Budget"].min()), float(df["Budget"].max()), (float(df["Budget"].min()), float(df["Budget"].max())))

    filtered_df = df.copy()
    filtered_df = filtered_df[
        (filtered_df["Year"] >= year_range[0]) &
        (filtered_df["Year"] <= year_range[1]) &
        (filtered_df["Box Office"] >= box_range[0]) &
        (filtered_df["Box Office"] <= box_range[1]) &
        (filtered_df["Budget"] >= budget_range[0]) &
        (filtered_df["Budget"] <= budget_range[1])
    ]

    if genres:
        filtered_df = filtered_df[filtered_df["Genre"].apply(lambda x: any(g in x for g in genres))]

    if directors:
        filtered_df = filtered_df[filtered_df["Director"].isin(directors)]

    if actors:
        filtered_df = filtered_df[filtered_df["Cast"].apply(lambda x: any(a in x for a in actors))]

    st.subheader("🎬 Ratings Distribution")
    rating_type = st.selectbox("Select Rating Type", ["IMDB Rating", "Rotten Percent", "Metacritic Score"])
    st.altair_chart(
        alt.Chart(filtered_df.dropna(subset=[rating_type]))
        .mark_bar()
        .encode(
            x=alt.X(f"{rating_type}:Q", bin=True, title=rating_type),
            y=alt.Y("count()", title="Count"),
            color=alt.value(PALETTE[0])
        ).properties(width=600, height=300),
        use_container_width=True
    )

    st.subheader("📊 IMDB vs Rotten Tomatoes (bubble = Metacritic)")
    scatter = alt.Chart(filtered_df.dropna(subset=["IMDB Rating", "Rotten Percent", "Metacritic Score"])).mark_circle().encode(
        x=alt.X("IMDB Rating:Q", scale=alt.Scale(zero=False)),
        y=alt.Y("Rotten Percent:Q", scale=alt.Scale(zero=False)),
        size="Metacritic Score:Q",
        color=alt.Color("Metacritic Score:Q", scale=alt.Scale(scheme='reds')),
        tooltip=["Title", "Year", "Director", "IMDB Rating", "Rotten Percent", "Metacritic Score"]
    ).properties(width=700, height=400)
    st.altair_chart(scatter, use_container_width=True)

    st.subheader("🏆 Top 10 Summary")
    category = st.selectbox("Group By", ["Year", "Genre", "Cast", "Director"])
    exploded_df = df.explode(category) if category in ["Genre", "Cast"] else df
    summary = exploded_df.groupby(category).agg({
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

    st.subheader("🧠 Bubble Chart by Category")
    category = st.selectbox("Category for Grouping", ["Genre", "Year", "Cast", "Director"])
    bubble_df = df.explode(category) if category in ["Genre", "Cast"] else df
    group = bubble_df.groupby(category).agg({
        "IMDB Rating": "mean",
        "Rotten Percent": "mean",
        "Metacritic Score": "mean",
        "Title": "count"
    }).rename(columns={"Title": "Movie Count"}).reset_index()
    group = group.dropna()

    chart = alt.Chart(group).mark_circle().encode(
        x=alt.X("IMDB Rating:Q", scale=alt.Scale(zero=False)),
        y=alt.Y("Rotten Percent:Q", scale=alt.Scale(zero=False)),
        size=alt.Size("Movie Count:Q", legend=None),
        color=alt.Color("Metacritic Score:Q", scale=alt.Scale(scheme="blues")),
        tooltip=[category, "Movie Count", "IMDB Rating", "Rotten Percent", "Metacritic Score"]
    ).properties(width=700, height=400)
    st.altair_chart(chart, use_container_width=True)

    st.subheader("💸 Box Office vs Budget")
    scatter_box = alt.Chart(filtered_df.dropna(subset=["Box Office", "Budget", "IMDB Rating", "Rotten Percent"])).mark_circle().encode(
        x="Budget:Q",
        y="Box Office:Q",
        color=alt.Color("IMDB Rating:Q", scale=alt.Scale(scheme="purpleorange")),
        size="Rotten Percent:Q",
        tooltip=["Title", "Box Office", "Budget", "IMDB Rating", "Rotten Percent"]
    ).properties(width=700, height=400)
    st.altair_chart(scatter_box, use_container_width=True)

    st.subheader("📈 Movies Over Time")
    rating_metric = st.selectbox("Select Rating for Overlay", ["IMDB Rating", "Rotten Percent", "Metacritic Score"])
    timeline = filtered_df.groupby("Year").agg({
        "Title": "count",
        rating_metric: "mean"
    }).rename(columns={"Title": "Movie Count"}).reset_index()

    base = alt.Chart(timeline).encode(x="Year:O")
    bar = base.mark_bar(color=PALETTE[1]).encode(y=alt.Y("Movie Count:Q", axis=alt.Axis(title="Movie Count")))
    line = base.mark_line(color=PALETTE[2], strokeWidth=3).encode(y=alt.Y(f"{rating_metric}:Q", axis=alt.Axis(title=rating_metric)))

    st.altair_chart((bar + line).resolve_scale(y='independent'), use_container_width=True)
