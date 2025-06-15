import streamlit as st
import pandas as pd
import altair as alt
import ast

def analytics_tab(df, show_filters=False):
    st.header("🎬 Analytics Dashboard")

    # Parse Genre and Cast
    def parse_list_column(col):
        return col.apply(
            lambda x: [s.strip() for s in x.split(",")] if isinstance(x, str) and "," in x else
            ast.literal_eval(x) if isinstance(x, str) and x.startswith("[") else
            [] if pd.isna(x) else [x]
        )

    # Parse Genre and Cast
    df["Genre"] = parse_list_column(df.get("Genre", pd.Series([])))
    df["Cast"] = parse_list_column(df.get("Cast", pd.Series([])))
    
    # Sanity check to ensure they’re all lists
    df["Genre"] = df["Genre"].apply(lambda x: x if isinstance(x, list) else [])
    df["Cast"] = df["Cast"].apply(lambda x: x if isinstance(x, list) else [])
    
    # Generate unique lists
    all_genres = sorted({g for genres in df["Genre"] for g in genres if isinstance(g, str)})
    all_cast = sorted({c for cast in df["Cast"] for c in cast if isinstance(c, str)})
    all_directors = sorted(df["Director"].dropna().unique())

    
    # Normalize numeric columns
    for col in ["IMDB Rating", "Rotten Tomatoes", "Metacritic Score"]:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace("%", "").str.strip(), errors="coerce")

    for money_col in ["Box Office", "Budget"]:
        df[money_col] = pd.to_numeric(df[money_col].astype(str).str.replace("[$,]", "", regex=True), errors="coerce")

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")

    # === Filters ===
    st.subheader("🔍 Filters")
    col1, col2, col3 = st.columns(3)
    with col1:
        year_range = st.slider("Year", int(df["Year"].min()), int(df["Year"].max()), (int(df["Year"].min()), int(df["Year"].max())))
        genre_filter = st.multiselect("Genres", all_genres)
    with col2:
        budget_range = st.slider("Budget ($)", int(df["Budget"].min()), int(df["Budget"].max()), (int(df["Budget"].min()), int(df["Budget"].max())))
        director_filter = st.multiselect("Directors", all_directors)
    with col3:
        box_office_range = st.slider("Box Office ($)", int(df["Box Office"].min()), int(df["Box Office"].max()), (int(df["Box Office"].min()), int(df["Box Office"].max())))
        actor_filter = st.multiselect("Actors", all_cast)
    
    def matches(row):
        return (
            year_range[0] <= row["Year"] <= year_range[1]
            and budget_range[0] <= row["Budget"] <= budget_range[1]
            and box_office_range[0] <= row["Box Office"] <= box_office_range[1]
            and (not genre_filter or any(g in row["Genre"] for g in genre_filter))
            and (not director_filter or row["Director"] in director_filter)
            and (not actor_filter or any(a in row["Cast"] for a in actor_filter))
        )
    
    filtered_df = df[df.apply(matches, axis=1)].copy()

    # === Ratings Histogram ===
    rating_col = st.selectbox("Rating Type", ["IMDB Rating", "Rotten Tomatoes", "Metacritic Score"])
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
        exploded = df.explode(summary_group)
    else:
        exploded = df.copy()

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
    bubble_df = df.explode(bubble_cat) if bubble_cat in ["Genre", "Cast"] else df

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
        df.groupby("Year")
        .agg(
            count=("Title", "count"),
            avg_rating=(rating_axis, "mean")
        )
        .dropna()
        .reset_index()
    )

    base = alt.Chart(year_df).encode(x="Year:O")

    bar = base.mark_bar().encode(y="count")
    line = base.mark_line(color="#b02711").encode(y=alt.Y("avg_rating", axis=alt.Axis(title="Avg Rating")))

    st.altair_chart((bar + line).resolve_scale(y="independent").properties(height=400), use_container_width=True)
