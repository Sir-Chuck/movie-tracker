import streamlit as st
import pandas as pd
import altair as alt

def analytics_tab(df):
    if df.empty:
        st.warning("No data available for analytics.")
        return

    # Clean and convert fields
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["IMDB Rating"] = pd.to_numeric(df["IMDB Rating"], errors="coerce")
    df["Metacritic Score"] = pd.to_numeric(df["Metacritic Score"], errors="coerce")
    df["Rotten Percent"] = df["Rotten Tomatoes"].str.replace("%", "", regex=False).astype(float)
    df["Box Office"] = pd.to_numeric(df["Box Office"].replace('[\$,]', '', regex=True), errors="coerce")
    df["Budget"] = pd.to_numeric(df["Budget"].replace('[\$,]', '', regex=True), errors="coerce")

    # Explode genres and cast for summaries
    df["Genre"] = df["Genre"].apply(lambda x: eval(x) if isinstance(x, str) else x)
    df["Cast"] = df["Cast"].apply(lambda x: eval(x) if isinstance(x, str) else x)
    df_exp_genre = df.explode("Genre")
    df_exp_cast = df.explode("Cast")

    # Sidebar filters
    with st.sidebar:
        st.markdown("### Filters")
        year_min, year_max = int(df["Year"].min()), int(df["Year"].max())
        year_range = st.slider("Year Range", year_min, year_max, (year_min, year_max))
        genre_filter = st.multiselect("Genre", sorted(set(g for sub in df["Genre"].dropna() for g in sub)))
        director_filter = st.selectbox("Director", ["All"] + sorted(df["Director"].dropna().unique()))
        actor_filter = st.selectbox("Actor", ["All"] + sorted(set(a for sub in df["Cast"].dropna() for a in sub)))

    # Apply filters
    filtered = df.copy()
    filtered = filtered[(filtered["Year"] >= year_range[0]) & (filtered["Year"] <= year_range[1])]
    if genre_filter:
        filtered = filtered[filtered["Genre"].apply(lambda genres: any(g in genres for g in genre_filter))]
    if director_filter != "All":
        filtered = filtered[filtered["Director"] == director_filter]
    if actor_filter != "All":
        filtered = filtered[filtered["Cast"].apply(lambda actors: actor_filter in actors)]

    st.markdown("### Ratings Distribution")
    rating_type = st.selectbox("Select Rating Type", ["IMDB Rating", "Metacritic Score", "Rotten Percent"])
    hist = alt.Chart(filtered).mark_bar().encode(
        x=alt.X(rating_type, bin=alt.Bin(maxbins=25), title=rating_type),
        y=alt.Y('count()', title="Movie Count"),
        tooltip=[rating_type, 'count()'],
        color=alt.value("#f27802")
    ).properties(height=300)
    st.altair_chart(hist, use_container_width=True)

    st.markdown("### IMDB vs Rotten Tomatoes (bubble by Metacritic)")
    scatter = alt.Chart(filtered).mark_circle().encode(
        x=alt.X("IMDB Rating", scale=alt.Scale(zero=False)),
        y=alt.Y("Rotten Percent", scale=alt.Scale(zero=False)),
        size="Metacritic Score",
        color="Metacritic Score",
        tooltip=["Title", "IMDB Rating", "Rotten Percent", "Metacritic Score", "Year", "Director"]
    ).interactive().properties(height=400)
    st.altair_chart(scatter, use_container_width=True)

    st.markdown("### Top 10 Summary")
    group_choice = st.selectbox("Top 10 By", ["Genre", "Director", "Cast", "Year"])
    if group_choice == "Genre":
        summary_df = df_exp_genre
        group_col = "Genre"
    elif group_choice == "Cast":
        summary_df = df_exp_cast
        group_col = "Cast"
    else:
        summary_df = df
        group_col = group_choice

    top10 = summary_df.groupby(group_col).agg(
        Movie_Count=("Title", "count"),
        Avg_IMDB=("IMDB Rating", "mean"),
        Avg_RT=("Rotten Percent", "mean"),
        Avg_Meta=("Metacritic Score", "mean"),
        Avg_BoxOffice=("Box Office", "mean"),
        Total_BoxOffice=("Box Office", "sum")
    ).sort_values("Movie_Count", ascending=False).head(10)

    top10 = top10.round({
        "Avg_IMDB": 2, "Avg_RT": 2, "Avg_Meta": 2, "Avg_BoxOffice": 2, "Total_BoxOffice": 2
    })
    top10["Avg_BoxOffice"] = top10["Avg_BoxOffice"].map("${:,.2f}".format)
    top10["Total_BoxOffice"] = top10["Total_BoxOffice"].map("${:,.2f}".format)
    st.dataframe(top10)

    st.markdown("### Box Office vs Budget (colored by IMDB)")
    box = alt.Chart(filtered).mark_circle().encode(
        x=alt.X("Budget", title="Budget ($)", scale=alt.Scale(zero=False)),
        y=alt.Y("Box Office", title="Box Office ($)", scale=alt.Scale(zero=False)),
        color="IMDB Rating",
        size="Rotten Percent",
        tooltip=["Title", "Budget", "Box Office", "IMDB Rating", "Rotten Percent"]
    ).interactive().properties(height=400)
    st.altair_chart(box, use_container_width=True)

    st.markdown("### Movies Over Time")
    rating_metric = st.selectbox("Average Rating Metric", ["IMDB Rating", "Rotten Percent", "Metacritic Score"])
    yearly = filtered.groupby("Year").agg(
        Movie_Count=("Title", "count"),
        Avg_Rating=(rating_metric, "mean")
    ).dropna()

    base = alt.Chart(yearly.reset_index()).encode(x=alt.X("Year:O", title="Year", axis=alt.Axis(format="d")))
    bars = base.mark_bar(color="#f27802").encode(y=alt.Y("Movie_Count", axis=alt.Axis(title="Movie Count")))
    line = base.mark_line(color="#2e0854").encode(
        y=alt.Y("Avg_Rating", axis=alt.Axis(title="Average Rating"), scale=alt.Scale(zero=False))
    )
    st.altair_chart(bars + line, use_container_width=True)
