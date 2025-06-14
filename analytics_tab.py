# analytics_tab.py
import streamlit as st
import pandas as pd
import altair as alt

def analytics_tab(df):
    st.subheader("Analytics")

    if df.empty:
        st.info("No data to analyze. Add movies first.")
        return

    # Filters (only appear here)
    with st.sidebar:
        st.markdown("### Filter Options")
        year_min, year_max = int(df["Year"].min()), int(df["Year"].max())
        year_range = st.slider("Release Year", min_value=year_min, max_value=year_max, value=(year_min, year_max))

        all_genres = sorted({g.strip() for sublist in df["Genre"].dropna().str.split(",") for g in sublist})
        selected_genres = st.multiselect("Genres", all_genres)

        budget_range = st.slider("Budget ($)", min_value=0, max_value=int(df["Budget"].max()), value=(0, int(df["Budget"].max())))
        box_range = st.slider("Box Office ($)", min_value=0, max_value=int(df["Box Office"].max()), value=(0, int(df["Box Office"].max())))

        directors = df["Director"].dropna().unique()
        selected_director = st.selectbox("Director (Autocomplete)", [""] + sorted(directors.tolist()))

        actors = sorted({actor.strip() for sublist in df["Cast"].dropna().str.split(",") for actor in sublist})
        selected_actor = st.selectbox("Actor (Autocomplete)", [""] + actors)

    # Apply filters
    filtered_df = df.copy()
    filtered_df = filtered_df[(filtered_df["Year"] >= year_range[0]) & (filtered_df["Year"] <= year_range[1])]
    filtered_df = filtered_df[(filtered_df["Budget"] >= budget_range[0]) & (filtered_df["Budget"] <= budget_range[1])]
    filtered_df = filtered_df[(filtered_df["Box Office"] >= box_range[0]) & (filtered_df["Box Office"] <= box_range[1])]
    if selected_genres:
        filtered_df = filtered_df[filtered_df["Genre"].apply(lambda x: any(g in x for g in selected_genres) if pd.notna(x) else False)]
    if selected_director:
        filtered_df = filtered_df[filtered_df["Director"] == selected_director]
    if selected_actor:
        filtered_df = filtered_df[filtered_df["Cast"].apply(lambda x: selected_actor in x if pd.notna(x) else False)]

    if filtered_df.empty:
        st.warning("No results match your filter criteria.")
        return

    # Distribution Histogram
    st.markdown("### 🎯 Ratings Distribution")
    rating_type = st.selectbox("Select Rating Type", ["IMDB Rating", "Rotten Tomatoes", "Metacritic Score"])
    chart = alt.Chart(filtered_df).mark_bar().encode(
        alt.X(f"{rating_type}:Q", bin=True),
        y='count()',
        tooltip=[rating_type]
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)

    # Ratings Scatter Plot
    st.markdown("### 🎯 IMDB vs Rotten Tomatoes")
    chart = alt.Chart(filtered_df).mark_circle().encode(
        x=alt.X("IMDB Rating", scale=alt.Scale(zero=False)),
        y=alt.Y("Rotten Tomatoes", scale=alt.Scale(zero=False)),
        size="Metacritic Score",
        color="Metacritic Score",
        tooltip=["Title", "Year", "Director", "IMDB Rating", "Rotten Tomatoes", "Metacritic Score"]
    ).properties(height=400)
    st.altair_chart(chart, use_container_width=True)

    # Top Ten Table
    st.markdown("### 🎯 Top Ten Summary Table")
    category = st.selectbox("Group by", ["Year", "Genre", "Cast", "Director"])
    group = filtered_df.explode(category if category != "Year" else None)
    top10 = group.groupby(category).agg({
        "Title": "count",
        "IMDB Rating": "mean",
        "Rotten Tomatoes": "mean",
        "Metacritic Score": "mean",
        "Box Office": "sum"
    }).rename(columns={"Title": "Movie Count"}).sort_values("Movie Count", ascending=False).head(10)
    st.dataframe(top10.style.format({
        "IMDB Rating": "{:.2f}",
        "Rotten Tomatoes": "{:.2f}",
        "Metacritic Score": "{:.2f}",
        "Box Office": "${:,.2f}"
    }), use_container_width=True)

    # Multi-dimension Bubble
    st.markdown("### 🎯 Ratings by Group")
    group_option = st.selectbox("Choose Category", ["Genre", "Year", "Cast", "Director"])
    grouped = filtered_df.explode(group_option) if group_option != "Year" else filtered_df.copy()
    grouped = grouped.groupby(group_option).agg({
        "IMDB Rating": "mean",
        "Rotten Tomatoes": "mean",
        "Metacritic Score": "mean",
        "Title": "count"
    }).rename(columns={"Title": "Movie Count"}).reset_index()

    chart = alt.Chart(grouped).mark_circle().encode(
        x="IMDB Rating",
        y="Rotten Tomatoes",
        size="Movie Count",
        color="Metacritic Score",
        tooltip=[group_option, "Movie Count", "IMDB Rating", "Rotten Tomatoes", "Metacritic Score"]
    ).properties(height=400)
    st.altair_chart(chart, use_container_width=True)

    # Budget vs Box Office
    st.markdown("### 🎯 Box Office vs Budget")
    chart = alt.Chart(filtered_df).mark_circle().encode(
        x=alt.X("Budget", scale=alt.Scale(zero=False)),
        y=alt.Y("Box Office", scale=alt.Scale(zero=False)),
        size="Rotten Tomatoes",
        color="IMDB Rating",
        tooltip=["Title", "Budget", "Box Office", "IMDB Rating", "Rotten Tomatoes"]
    ).properties(height=400)
    st.altair_chart(chart, use_container_width=True)

    # Movies Over Time
    st.markdown("### 🎯 Movies Over Time")
    rating_choice = st.selectbox("Select Rating for Avg Line", ["IMDB Rating", "Rotten Tomatoes", "Metacritic Score"])
    yearly = filtered_df.groupby("Year").agg({
        "Title": "count",
        rating_choice: "mean"
    }).rename(columns={"Title": "Movie Count"}).reset_index()

    bars = alt.Chart(yearly).mark_bar(color="#7786c8").encode(
        x="Year:O",
        y="Movie Count"
    )
    line = alt.Chart(yearly).mark_line(color="#f27802").encode(
        x="Year:O",
        y=alt.Y(f"{rating_choice}:Q", axis=alt.Axis(title=f"Avg {rating_choice}"))
    )
    st.altair_chart(bars + line, use_container_width=True)
