import streamlit as st
import pandas as pd
import altair as alt
from filters import apply_filters

def analytics_tab(df):
    st.header("🎬 Analytics Dashboard")

    # Apply filters and get filtered dataframe
    filtered_df, _ = apply_filters(df)

    st.write("Rows in DataFrame:", len(df))

    # === Ratings Histogram ===
    rating_col = st.selectbox("Rating Type", ["IMDB Rating", "Rotten Tomatoes", "Metacritic Score"])
    if not filtered_df.empty and rating_col in filtered_df.columns:
        st.altair_chart(
            alt.Chart(filtered_df.dropna(subset=[rating_col])).mark_bar().encode(
                x=alt.X(rating_col, bin=True),
                y="count()",
                tooltip=[rating_col]
            ).properties(height=300),
            use_container_width=True
        )

    # === Ratings Scatter ===
    scatter_df = filtered_df.dropna(subset=["IMDB Rating", "Rotten Tomatoes", "Metacritic Score"])
    if not scatter_df.empty:
        st.altair_chart(
            alt.Chart(scatter_df).mark_circle().encode(
                x="IMDB Rating",
                y="Rotten Tomatoes",
                size=alt.Size("Metacritic Score", scale=alt.Scale(range=[10, 400])),
                color="Metacritic Score",
                tooltip=["Title", "Year", "Director", "IMDB Rating", "Rotten Tomatoes", "Metacritic Score"]
            ).properties(height=400),
            use_container_width=True
        )

    # === Top 10 Tables ===
    st.subheader("🏆 Top 10 Summary")
    summary_group = st.selectbox("Top 10 by", ["Year", "Genre", "Director", "Cast"])
    if summary_group in ["Genre", "Cast"]:
        exploded = filtered_df.explode(summary_group)
    else:
        exploded = filtered_df.copy()

    if not exploded.empty:
        top_agg = (
            exploded.groupby(summary_group)
            .agg(
                Movie_Count=("Title", "count"),
                Avg_IMDB=("IMDB Rating", "mean"),
                Avg_RT=("Rotten Tomatoes", "mean"),
                Avg_MC=("Metacritic Score", "mean"),
                Total_Box=("Box Office", "sum")
            )
            .dropna()
            .sort_values("Movie_Count", ascending=False)
            .head(10)
            .round(2)
        )

        top_agg["Total_Box"] = top_agg["Total_Box"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(top_agg)

    # === Category Scatterplot ===
    st.subheader("📈 Ratings by Category")
    bubble_cat = st.selectbox("Bubble Category", ["Genre", "Year", "Director", "Cast"])
    bubble_df = filtered_df.explode(bubble_cat) if bubble_cat in ["Genre", "Cast"] else filtered_df

    grouped = (
        bubble_df.groupby(bubble_cat)
        .agg(
            avg_rt=("Rotten Tomatoes", "mean"),
            avg_imdb=("IMDB Rating", "mean"),
            avg_mc=("Metacritic Score", "mean"),
            count=("Title", "count")
        )
        .dropna()
        .reset_index()
        .round(2)
    )

    if not grouped.empty:
        st.altair_chart(
            alt.Chart(grouped).mark_circle().encode(
                x="avg_imdb",
                y="avg_rt",
                size="count",
                color="avg_mc",
                tooltip=[bubble_cat, "avg_rt", "avg_imdb", "avg_mc", "count"]
            ).properties(height=400),
            use_container_width=True
        )

    # === Budget vs Box Office ===
    st.subheader("💰 Budget vs Box Office")
    bo_df = filtered_df.dropna(subset=["Box Office", "Budget", "IMDB Rating", "Rotten Tomatoes"])
    if not bo_df.empty:
        st.altair_chart(
            alt.Chart(bo_df).mark_circle().encode(
                x=alt.X("Budget", scale=alt.Scale(zero=False)),
                y=alt.Y("Box Office", scale=alt.Scale(zero=False)),
                size="Rotten Tomatoes",
                color="IMDB Rating",
                tooltip=["Title", "Year", "Budget", "Box Office", "IMDB Rating", "Rotten Tomatoes"]
            ).properties(height=400),
            use_container_width=True
        )

    # === Dual Axis Chart ===
    st.subheader("📊 Movies Per Year vs Avg Rating")
    rating_axis = st.selectbox("Select Rating", ["IMDB Rating", "Rotten Tomatoes", "Metacritic Score"])
    year_df = (
        filtered_df.groupby("Year")
        .agg(
            count=("Title", "count"),
            avg_rating=(rating_axis, "mean")
        )
        .dropna()
        .reset_index()
    )

    if not year_df.empty:
        base = alt.Chart(year_df).encode(x="Year:O")

        bar = base.mark_bar().encode(y="count")
        line = base.mark_line(color="#b02711").encode(y=alt.Y("avg_rating", axis=alt.Axis(title="Avg Rating")))

        st.altair_chart((bar + line).resolve_scale(y="independent").properties(height=400), use_container_width=True)
