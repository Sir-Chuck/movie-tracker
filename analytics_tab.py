import streamlit as st
import pandas as pd
import altair as alt
import ast

def analytics_tab(df):
    # === Branding Styles ===
    st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-family: Verdana, sans-serif;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("## <span style='color:#2e0854'>🎬 Analytics Dashboard</span>", unsafe_allow_html=True)

    # === Parsing ===
    def parse_list_column(col):
        return col.apply(lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith("[") else [])

    df["Genre"] = parse_list_column(df.get("Genre", pd.Series([])))
    df["Cast"] = parse_list_column(df.get("Cast", pd.Series([])))

    for col in ["IMDB Rating", "Rotten Tomatoes", "Metacritic Score"]:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace("%", "").str.strip(), errors="coerce")
    for money_col in ["Box Office", "Budget"]:
        df[money_col] = pd.to_numeric(df[money_col].astype(str).str.replace("[$,]", "", regex=True), errors="coerce")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")

    # === Filters Sidebar ===
    with st.sidebar:
        st.markdown("## <span style='color:#f27802'>🔍 Filters</span>", unsafe_allow_html=True)

        all_genres = sorted({g for genres in df["Genre"].dropna() for g in genres})
        all_cast = sorted({c for cast in df["Cast"].dropna() for c in cast})
        all_directors = sorted(df["Director"].dropna().unique())

        year_range = st.slider("Year", int(df["Year"].min()), int(df["Year"].max()),
                               (int(df["Year"].min()), int(df["Year"].max())))
        genre_filter = st.multiselect("Genres", all_genres)
        budget_range = st.slider("Budget ($)", int(df["Budget"].min()), int(df["Budget"].max()),
                                 (int(df["Budget"].min()), int(df["Budget"].max())))
        box_office_range = st.slider("Box Office ($)", int(df["Box Office"].min()), int(df["Box Office"].max()),
                                     (int(df["Box Office"].min()), int(df["Box Office"].max())))
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
    color_scale = alt.Scale(range=["#f27802", "#2e0854", "#7786c8", "#708090", "#b02711"])

    # === Ratings Histogram ===
    rating_col = st.selectbox("Rating Type", ["IMDB Rating", "Rotten Tomatoes", "Metacritic Score"])
    st.altair_chart(
        alt.Chart(filtered_df.dropna(subset=[rating_col])).mark_bar().encode(
            x=alt.X(rating_col, bin=True),
            y="count()",
            tooltip=[rating_col],
            color=alt.value("#2e0854")
        ).properties(height=300),
        use ​:contentReference[oaicite:0]{index=0}​
