import streamlit as st
import pandas as pd
import altair as alt
import ast

def analytics_tab(df):
    st.markdown(
        """
        <style>
        html, body, [class*="css"] {
            font-family: Verdana !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.header("🎬 Analytics Dashboard")

    # Parse Genre and Cast columns
    def parse_list_column(col):
        return col.apply(
            lambda x: [s.strip() for s in x.split(",")] if isinstance(x, str) and "," in x else
            ast.literal_eval(x) if isinstance(x, str) and x.startswith("[") else
            [] if pd.isna(x) else [x]
        )

    df["Genre"] = parse_list_column(df.get("Genre", pd.Series([])))
    df["Cast"] = parse_list_column(df.get("Cast", pd.Series([])))

    # Normalize columns
    for col in ["IMDB Rating", "Rotten Tomatoes", "Metacritic Score"]:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace("%", "").str.strip(), errors="coerce")

    for money_col in ["Box Office", "Budget"]:
        df[money_col] = pd.to_numeric(df[money_col].astype(str).str.replace("[$,]", "", regex=True), errors="coerce")

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")

    # Unique filter values
    all_genres = sorted({g for genres in df["Genre"] for g in genres if isinstance(g, str)})
    all_cast = sorted({c for cast in df["Cast"] for c in cast if isinstance(c, str)})
    all_directors = sorted(df["Director"].dropna().unique())

    # === Filters ===
    st.subheader("🔍 Filters")
    col1, col2, col3 = st.columns(3)
    with col1:
        year_range = st.slider("Year", int(df["Year"].min()), int(df["Year"].max()),
                               (int(df["Year"].min()), int(df["Year"].max())))
        genre_filter = st.multiselect("Genres", all_genres)
    with col2:
        budget_range = st.slider("Budget ($)", int(df["Budget"].min()), int(df["Budget"].max()),
                                 (int(df["Budget"].min()), int(df["Budget"].max())))
        box_office_range = st.slider("Box Office ($)", int(df["Box Office"].min()), int(df["Box Office"].max()),
                                     (int(df["Box Office"].min()), int(df["Box Office"].max())))
    with col3:
        director_filter = st.multiselect("Directors", all_directors)
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
    st.altair_chart(
        alt.Chart(filtered_df.dropna(subset=["IMDB Rating", "Rotten Tomatoes", "Metacritic Score"]))
        .mark_circle()
        .encode(
            x="IMDB Rating",
            y="Rotten Tomatoes",
            size=alt.Size("Metacritic Score", scale=alt.Scale(range=[10, 400])),
            color=alt.Color("Metacritic Score", scale=alt.Scale(scheme='purpleorange')),
            tooltip=["Title", "Year", "Director", "IMDB Rating", "Rotten Tomatoes", "Metacritic Score"]
        )
        .properties(height=400),
        use_container_width=True
    )

    # === Top 10 Summary Table ===
    st.subheader("🏆 Top 10 Summary")
    group_by = st.selectbox("Top 10 by", ["Year", "Genre", "Director", "Cast"])
    exploded = df.explode(group_by) if group_by in ["Genre", "Cast"] else df

    top_10 = (
        exploded.groupby(group_by)
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
    top_10["Total_Box"] = top_10["Total_Box"].apply(lambda x: f"${x:,.0f}")
    st.dataframe(top_10)

    # === Ratings by Category Bubble Chart ===
    st.subheader("📈 Ratings by Category")
    bubble_cat = st.selectbox("Bubble Category", ["Genre", "Year", "Director", "Cast"])
    exploded_cat = df.explode(bubble_cat) if bubble_cat in ["Genre", "Cast"] else df

    bubble_df = (
        exploded_cat.groupby(bubble_cat)
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
        alt.Chart(bubble_df).mark_circle().encode(
            x="avg_imdb",
            y="avg_rt",
            size="count",
            color=alt.Color("avg_mc", scale=alt.Scale(range=["#f27802", "#2e0854", "#7786c8", "#708090", "#b02711"])),
            tooltip=[bubble_cat, "avg_rt", "avg_imdb", "avg_mc", "count"]
        ).properties(height=400),
        use_container_width=True
    )

    # === Budget vs. Box Office ===
    st.subheader("💰 Budget vs Box Office")
    bo_df = filtered_df.dropna(subset=["Box Office", "Budget"])
    st.altair_chart(
        alt.Chart(bo_df).mark_circle().encode(
            x=alt.X("Budget", scale=alt.Scale(zero=False)),
            y=alt.Y("Box Office", scale=alt.Scale(zero=False)),
            size="Rotten Tomatoes",
            color=alt.Color("IMDB Rating", scale=alt.Scale(range=["#f27802", "#2e0854", "#7786c8", "#708090", "#b02711"])),
            tooltip=["Title", "Year", "Budget", "Box Office"]
        ).properties(height=400),
        use_container_width=True
    )

    # === Dual Axis Chart: Movies per Year vs Rating ===
    st.subheader("📊 Movies Per Year vs Avg Rating")
    rating_axis = st.selectbox("Rating Axis", ["IMDB Rating", "Rotten Tomatoes", "Metacritic Score"])
    yearly = (
        df.groupby("Year")
        .agg(count=("Title", "count"), avg_rating=(rating_axis, "mean"))
        .dropna()
        .reset_index()
    )

    base = alt.Chart(yearly).encode(x="Year:O")
    bar = base.mark_bar().encode(y="count")
    line = base.mark_line(color="#b02711").encode(y=alt.Y("avg_rating", axis=alt.Axis(title="Avg Rating")))
    st.altair_chart((bar + line).resolve_scale(y="independent").properties(height=400), use_container_width=True)
