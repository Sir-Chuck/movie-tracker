import streamlit as st
import pandas as pd
import altair as alt

def explode_column(df, col):
    df = df.dropna(subset=[col]).copy()
    df[col] = df[col].astype(str).str.split(',')
    df = df.explode(col)
    df[col] = df[col].str.strip()
    return df

def render_analytics_tab(df, palette):
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

    rating_fields = {
        "IMDB Rating": "IMDB Rating",
        "Rotten Tomatoes": "Rotten Tomatoes",
        "Metacritic Score": "Metacritic Score"
    }

    rating_choice = st.selectbox("Select Rating for Histogram", list(rating_fields.keys()))
    valid_col = rating_fields[rating_choice]
    hist_df = filtered_df.dropna(subset=[valid_col])
    if not hist_df.empty:
        st.altair_chart(
            alt.Chart(hist_df).mark_bar(color=palette[0]).encode(
                x=alt.X(f"{valid_col}:Q", bin=True),
                y='count()'
            ).properties(title=f"Distribution of {rating_choice}", width=600),
            use_container_width=True
        )
    else:
        st.warning(f"No data for {rating_choice}")

    scatter_df = filtered_df.dropna(subset=["IMDB Rating", "Metacritic Score"])
    if not scatter_df.empty:
        st.altair_chart(
            alt.Chart(scatter_df).mark_circle().encode(
                x="IMDB Rating",
                y="Metacritic Score",
                color=alt.Color("Metacritic Score", scale=alt.Scale(scheme='redpurple')),
                size="Metacritic Score",
                tooltip=["Title", "IMDB Rating", "Rotten Tomatoes", "Metacritic Score", "Year", "Director"]
            ).properties(title="IMDB vs Metacritic Ratings", width=600),
            use_container_width=True
        )

    category = st.selectbox("Top 10 By", ["Year", "Genre", "Director", "Cast"])
    top_df = explode_column(filtered_df, category)
    summary = top_df.groupby(category).agg(
        Count=("Title", "count"),
        Avg_IMDB=("IMDB Rating", "mean"),
        Avg_RT=("Rotten Tomatoes", "mean"),
        Avg_Meta=("Metacritic Score", "mean"),
        Avg_Box=("Box Office", "mean"),
        Sum_Box=("Box Office", "sum")
    ).sort_values("Count", ascending=False).head(10).round(2).reset_index()
    st.dataframe(summary)

    group_col = st.selectbox("Bubble Chart Group By", ["Genre", "Year", "Director", "Cast"])
    grouped_df = explode_column(filtered_df, group_col)
    bubble = grouped_df.groupby(group_col).agg(
        Avg_IMDB=("IMDB Rating", "mean"),
        Avg_RT=("Rotten Tomatoes", "mean"),
        Avg_Meta=("Metacritic Score", "mean"),
        Count=("Title", "count")
    ).dropna().reset_index()
    st.altair_chart(
        alt.Chart(bubble).mark_circle().encode(
            x="Avg_IMDB",
            y="Avg_RT",
            size="Count",
            color=alt.Color("Avg_Meta", scale=alt.Scale(scheme='redpurple')),
            tooltip=[group_col, "Count", "Avg_IMDB", "Avg_RT", "Avg_Meta"]
        ).properties(title="Grouped Rating Comparison", width=600),
        use_container_width=True
    )

    scatter2_df = filtered_df.dropna(subset=["Budget", "Box Office", "IMDB Rating", "Rotten Tomatoes"])
    if not scatter2_df.empty:
        st.altair_chart(
            alt.Chart(scatter2_df).mark_circle().encode(
                x=alt.X("Budget", axis=alt.Axis(format="$,.2f")),
                y=alt.Y("Box Office", axis=alt.Axis(format="$,.2f")),
                size="Rotten Tomatoes",
                color=alt.Color("IMDB Rating", scale=alt.Scale(scheme='redpurple')),
                tooltip=["Title", "Budget", "Box Office", "IMDB Rating", "Rotten Tomatoes"]
            ).properties(title="Budget vs Box Office", width=600),
            use_container_width=True
        )

    metric_choice = st.selectbox("Metric for Average Rating", list(rating_fields.keys()))
    metric_col = rating_fields[metric_choice]
    yearly = filtered_df.groupby("Year").agg(
        Movie_Count=("Title", "count"),
        Avg_Rating=(metric_col, "mean")
    ).dropna().reset_index()
    base = alt.Chart(yearly).encode(x=alt.X("Year:O"))
    bars = base.mark_bar(color=palette[0]).encode(y="Movie_Count")
    line = base.mark_line(color=palette[2]).encode(y="Avg_Rating")
    st.altair_chart((bars + line).resolve_scale(y="independent").properties(title="Movies Over Time"), use_container_width=True)
