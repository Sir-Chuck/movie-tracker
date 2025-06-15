# analytics_tab.py
import streamlit as st
import pandas as pd
import altair as alt
import ast
import ast

def safe_parse_list(val):
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            parsed = ast.literal_eval(val)
            return parsed if isinstance(parsed, list) else []
        except (ValueError, SyntaxError):
            return []
    return []

def analytics_tab(df):
    st.subheader("📊 Analytics")

    if df.empty:
        st.info("No data to display.")
        return

    # Use safe parser for Genre and Cast
    df["Genre"] = df["Genre"].apply(safe_parse_list)
    df["Cast"] = df["Cast"].apply(safe_parse_list)

    # Flatten Genre and Cast for summary
    genre_df = df.explode("Genre")
    cast_df = df.explode("Cast")

    # Clean and convert
    df["Box Office"] = pd.to_numeric(df["Box Office"], errors="coerce")
    df["Budget"] = pd.to_numeric(df["Budget"], errors="coerce")
    df["IMDB Rating"] = pd.to_numeric(df["IMDB Rating"], errors="coerce")
    df["Metacritic Score"] = pd.to_numeric(df["Metacritic Score"], errors="coerce")

    df["Rotten Percent"] = df["Rotten Tomatoes"].str.replace("%", "", regex=True).astype(float)

    # Sidebar filters – only on Analytics tab
    with st.sidebar:
        st.header("Filter Movies")
        year_range = st.slider("Year", int(df["Year"].min()), int(df["Year"].max()), (int(df["Year"].min()), int(df["Year"].max())))
        genres = list(set(g for sub in df["Genre"] for g in sub))
        selected_genres = st.multiselect("Genres", genres, default=genres)
        budget_range = st.slider("Budget ($)", float(df["Budget"].min()), float(df["Budget"].max()), (float(df["Budget"].min()), float(df["Budget"].max())))
        box_range = st.slider("Box Office ($)", float(df["Box Office"].min()), float(df["Box Office"].max()), (float(df["Box Office"].min()), float(df["Box Office"].max())))
        directors = sorted(df["Director"].dropna().unique())
        selected_directors = st.multiselect("Directors", directors)
        all_cast = sorted(set(c for sub in df["Cast"] for c in sub))
        selected_actors = st.multiselect("Actors", all_cast)

    # Apply filters
    filtered_df = df[
        (df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1]) &
        (df["Budget"] >= budget_range[0]) & (df["Budget"] <= budget_range[1]) &
        (df["Box Office"] >= box_range[0]) & (df["Box Office"] <= box_range[1]) &
        (df["Genre"].apply(lambda g: any(x in g for x in selected_genres))) &
        (df["Director"].isin(selected_directors) if selected_directors else True) &
        (df["Cast"].apply(lambda c: any(x in c for x in selected_actors)) if selected_actors else True)
    ]

    # Ratings Histogram
    rating_type = st.selectbox("Select Rating for Histogram", ["IMDB Rating", "Rotten Percent", "Metacritic Score"])
    st.altair_chart(
        alt.Chart(filtered_df).mark_bar().encode(
            x=alt.X(f"{rating_type}:Q", bin=True, title=rating_type),
            y=alt.Y("count()", title="Movie Count"),
            tooltip=[rating_type, "count()"]
        ).properties(width=600, height=300).configure_mark(color="#f27802"),
        use_container_width=True
    )

    # Ratings Scatter
    st.altair_chart(
        alt.Chart(filtered_df).mark_circle().encode(
            x=alt.X("IMDB Rating", title="IMDB Rating"),
            y=alt.Y("Rotten Percent", title="Rotten Tomatoes %"),
            size=alt.Size("Metacritic Score", scale=alt.Scale(range=[20, 300])),
            color=alt.Color("Metacritic Score", scale=alt.Scale(scheme='redpurple')),
            tooltip=["Title", "Year", "Director", "IMDB Rating", "Metacritic Score", "Rotten Percent"]
        ).properties(width=700, height=400),
        use_container_width=True
    )

    # Top 10 Summary Table
    st.subheader("Top 10 Summary Table")
    top_n_option = st.selectbox("Group by:", options=["Year", "Genre", "Director", "Cast"])
    
    df_top = df.copy()
    
    # Explode multi-value fields before groupby
    if top_n_option in ["Genre", "Cast"]:
        df_top = df_top.explode(top_n_option)
    
    # Group and aggregate
    top_agg = (
        df_top.groupby(top_n_option, dropna=True)
        .agg(
            Movie_Count=("Title", "count"),
            Avg_IMDB=("IMDB Rating", "mean"),
            Avg_RT=("Rotten Tomatoes", "mean"),
            Avg_Meta=("Metacritic Score", "mean"),
            Avg_Box=("Box Office", "mean"),
            Total_Box=("Box Office", "sum")
        )
        .sort_values("Movie_Count", ascending=False)
        .head(10)
        .reset_index()
    )
    
    # Format
    top_agg["Avg_IMDB"] = top_agg["Avg_IMDB"].round(2)
    top_agg["Avg_RT"] = top_agg["Avg_RT"].round(2)
    top_agg["Avg_Meta"] = top_agg["Avg_Meta"].round(2)
    top_agg["Avg_Box"] = top_agg["Avg_Box"].apply(lambda x: f"${x:,.2f}")
    top_agg["Total_Box"] = top_agg["Total_Box"].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(top_agg, use_container_width=True)
    
    # Dual-axis: movies per year vs avg rating
    rating_axis = st.selectbox("Average Rating (Right Y-Axis)", ["IMDB Rating", "Rotten Percent", "Metacritic Score"])
    dual_df = df.groupby("Year").agg(
        Movie_Count=("Title", "count"),
        Avg_Rating=(rating_axis, "mean")
    ).reset_index()

    base = alt.Chart(dual_df).encode(x="Year:O")

    bar = base.mark_bar(color="#7786c8").encode(
        y=alt.Y("Movie_Count:Q", axis=alt.Axis(title="Movie Count"))
    )

    line = base.mark_line(color="#b02711").encode(
        y=alt.Y("Avg_Rating:Q", axis=alt.Axis(title=rating_axis))
    )

    st
