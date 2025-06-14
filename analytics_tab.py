import pandas as pd
import streamlit as st
import altair as alt

def analytics_tab(df):
    st.subheader("Analytics")

    if df.empty:
        st.warning("No data to analyze. Please add movies first.")
        return

    # Ensure columns are strings before using .str
    df["Box Office"] = pd.to_numeric(df["Box Office"].astype(str).str.replace("[$,]", "", regex=True), errors="coerce")
    df["Budget"] = pd.to_numeric(df["Budget"].astype(str).str.replace("[$,]", "", regex=True), errors="coerce")
    df["IMDB Rating"] = pd.to_numeric(df["IMDB Rating"], errors="coerce")
    df["Metacritic Score"] = pd.to_numeric(df["Metacritic Score"], errors="coerce")
    df["Rotten Percent"] = pd.to_numeric(df["Rotten Tomatoes"].astype(str).str.replace("%", ""), errors="coerce")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")

    # Filters – only visible on Analytics
    st.markdown("### Filters")
    col1, col2, col3 = st.columns([3, 3, 3])
    with col1:
        year_range = st.slider("Year", int(df["Year"].min()), int(df["Year"].max()), (int(df["Year"].min()), int(df["Year"].max())))
    with col2:
        all_genres = sorted(set(g.strip() for lst in df["Genre"].dropna().str.split(",") for g in lst))
        selected_genres = st.multiselect("Genres", all_genres)
    with col3:
        director_filter = st.text_input("Director (partial match)")

    filtered_df = df[
        df["Year"].between(year_range[0], year_range[1]) &
        df["Genre"].apply(lambda g: any(genre in g for genre in selected_genres) if selected_genres else True) &
        df["Director"].str.contains(director_filter, case=False, na=False)
    ]

    # Ratings Histogram
    st.markdown("### Ratings Distribution")
    rating_type = st.selectbox("Select Rating", ["IMDB Rating", "Metacritic Score", "Rotten Percent"])
    st.altair_chart(
        alt.Chart(filtered_df).mark_bar().encode(
            x=alt.X(f"{rating_type}:Q", bin=True),
            y="count()",
            tooltip=["count()"]
        ).properties(width=600, height=300),
        use_container_width=True
    )

    # Ratings Scatter
    st.markdown("### Ratings Scatter")
    scatter_df = filtered_df.dropna(subset=["IMDB Rating", "Rotten Percent", "Metacritic Score"])
    st.altair_chart(
        alt.Chart(scatter_df).mark_circle().encode(
            x="IMDB Rating:Q",
            y="Rotten Percent:Q",
            size=alt.Size("Metacritic Score:Q", scale=alt.Scale(range=[20, 400])),
            color=alt.Color("Metacritic Score:Q", scale=alt.Scale(scheme="purplebluegreen")),
            tooltip=["Title", "IMDB Rating", "Rotten Percent", "Metacritic Score", "Year", "Director"]
        ).interactive().properties(width=700, height=400),
        use_container_width=True
    )

    # Top Ten Table
    st.markdown("### Top 10 Summary")
    group_by = st.selectbox("Group by", ["Year", "Genre", "Director", "Cast"])
    summary = (
        filtered_df.explode(group_by if group_by != "Year" else None)
        .groupby(group_by)
        .agg(
            Movie_Count=('Title', 'count'),
            Avg_IMDB=('IMDB Rating', 'mean'),
            Avg_RT=('Rotten Percent', 'mean'),
            Avg_Meta=('Metacritic Score', 'mean'),
            Total_BoxOffice=('Box Office', 'sum'),
            Avg_BoxOffice=('Box Office', 'mean')
        ).sort_values("Movie_Count", ascending=False).head(10).round(2)
    )
    st.dataframe(summary)

    # Bubble Scatter
    st.markdown("### Bubble Chart by Group")
    category = st.selectbox("Bubble Group", ["Genre", "Year", "Director", "Cast"])
    bubble_df = (
        filtered_df.explode(category)
        .groupby(category)
        .agg(
            Count=('Title', 'count'),
            Avg_IMDB=('IMDB Rating', 'mean'),
            Avg_RT=('Rotten Percent', 'mean'),
            Avg_Meta=('Metacritic Score', 'mean')
        ).reset_index()
    ).dropna()
    st.altair_chart(
        alt.Chart(bubble_df).mark_circle().encode(
            x="Avg_IMDB:Q",
            y="Avg_RT:Q",
            size="Count:Q",
            color="Avg_Meta:Q",
            tooltip=[category, "Count", "Avg_IMDB", "Avg_RT", "Avg_Meta"]
        ).interactive().properties(width=700, height=400),
        use_container_width=True
    )

    # Budget vs Box Office
    st.markdown("### Box Office vs Budget")
    bb = filtered_df.dropna(subset=["Box Office", "Budget", "IMDB Rating", "Rotten Percent"])
    st.altair_chart(
        alt.Chart(bb).mark_circle().encode(
            x=alt.X("Budget:Q", axis=alt.Axis(format="$,.0f")),
            y=alt.Y("Box Office:Q", axis=alt.Axis(format="$,.0f")),
            size="Rotten Percent:Q",
            color="IMDB Rating:Q",
            tooltip=["Title", "Budget", "Box Office", "IMDB Rating", "Rotten Percent"]
        ).interactive().properties(width=700, height=400),
        use_container_width=True
    )

    # Movies Over Time
    st.markdown("### Movies Over Time")
    rating_choice = st.selectbox("Rating for Line Chart", ["IMDB Rating", "Rotten Percent", "Metacritic Score"])
    time_df = filtered_df.groupby("Year").agg(
        Count=('Title', 'count'),
        Avg_Rating=(rating_choice, 'mean')
    ).reset_index()
    base = alt.Chart(time_df).encode(x=alt.X("Year:O"))
    bar = base.mark_bar(color="#7786c8").encode(y=alt.Y("Count:Q", axis=alt.Axis(title="Movie Count")))
    line = base.mark_line(color="#f27802").encode(y=alt.Y("Avg_Rating:Q", axis=alt.Axis(title=rating_choice)))
    st.altair_chart((bar + line).resolve_scale(y="independent").properties(height=400), use_container_width=True)
