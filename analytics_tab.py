# analytics_tab.py

import streamlit as st
import pandas as pd
import altair as alt
import ast

def analytics_tab(df):
    st.subheader("Analytics")

    # Convert and explode list columns
    for col in ["Genre", "Cast"]:
        df[col] = df[col].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else [])
    df = df.explode("Genre")
    df = df.explode("Cast")

    # Convert numerical fields
    for col in ["IMDB Rating", "Rotten Tomatoes", "Metacritic Score", "Box Office", "Budget"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Sidebar-style filters shown only on Analytics tab
    with st.container():
        st.markdown("### Filters")

        year_min, year_max = int(df["Year"].min()), int(df["Year"].max())
        year_range = st.slider("Filter by Year", year_min, year_max, (year_min, year_max))

        genre_options = sorted(df["Genre"].dropna().unique().tolist())
        selected_genres = st.multiselect("Filter by Genre", genre_options, default=genre_options)

        budget_range = st.slider("Budget ($)", int(df["Budget"].min()), int(df["Budget"].max()),
                                 (int(df["Budget"].min()), int(df["Budget"].max())))
        box_office_range = st.slider("Box Office ($)", int(df["Box Office"].min()), int(df["Box Office"].max()),
                                     (int(df["Box Office"].min()), int(df["Box Office"].max())))

        director_options = sorted(df["Director"].dropna().unique().tolist())
        selected_directors = st.multiselect("Director", director_options)

        cast_options = sorted(df["Cast"].dropna().unique().tolist())
        selected_cast = st.multiselect("Actor", cast_options)

    # Apply filters
    filtered_df = df[
        (df["Year"].between(*year_range)) &
        (df["Genre"].isin(selected_genres)) &
        (df["Budget"].between(*budget_range)) &
        (df["Box Office"].between(*box_office_range))
    ]
    if selected_directors:
        filtered_df = filtered_df[filtered_df["Director"].isin(selected_directors)]
    if selected_cast:
        filtered_df = filtered_df[filtered_df["Cast"].isin(selected_cast)]

    # Ratings Distribution
    rating_metric = st.selectbox("Select rating source for distribution", ["IMDB Rating", "Rotten Tomatoes", "Metacritic Score"])
    hist = alt.Chart(filtered_df).mark_bar().encode(
        x=alt.X(f"{rating_metric}:Q", bin=True),
        y='count()',
        tooltip=[rating_metric]
    ).properties(title=f"{rating_metric} Distribution", width=600, height=400)
    st.altair_chart(hist, use_container_width=True)

    # Ratings Scatter
    scatter = alt.Chart(filtered_df).mark_circle().encode(
        x=alt.X('IMDB Rating', scale=alt.Scale(zero=False)),
        y=alt.Y('Rotten Tomatoes', scale=alt.Scale(zero=False)),
        size='Metacritic Score',
        color='Metacritic Score',
        tooltip=['Title', 'IMDB Rating', 'Rotten Tomatoes', 'Metacritic Score', 'Year', 'Director']
    ).properties(title="IMDB vs Rotten Tomatoes", width=700, height=500)
    st.altair_chart(scatter, use_container_width=True)

    # Top 10 Summary Table
    top_by = st.selectbox("Top 10 by", ["Year", "Genre", "Director", "Cast"])
    top_agg = (
        filtered_df.groupby(top_by)
        .agg(
            Movie_Count=("Title", "count"),
            Avg_IMDB=("IMDB Rating", "mean"),
            Avg_RT=("Rotten Tomatoes", "mean"),
            Avg_Meta=("Metacritic Score", "mean"),
            Total_Box=("Box Office", "sum")
        )
        .sort_values("Movie_Count", ascending=False)
        .head(10)
        .reset_index()
    )
    top_agg["Avg_IMDB"] = top_agg["Avg_IMDB"].round(2)
    top_agg["Avg_RT"] = top_agg["Avg_RT"].round(2)
    top_agg["Avg_Meta"] = top_agg["Avg_Meta"].round(2)
    top_agg["Total_Box"] = top_agg["Total_Box"].map("${:,.2f}".format)
    st.dataframe(top_agg)

    # Add more charts here as needed (Budget vs Box Office, Dual Axis Yearly Chart, etc.)
