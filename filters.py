# filters.py
import streamlit as st
import pandas as pd
import ast

def apply_filters(df):
    # Ensure proper formatting
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Genre"] = df["Genre"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith("[") else [])
    df["Cast"] = df["Cast"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith("[") else [])

    all_genres = sorted({g for genres in df["Genre"].dropna() for g in genres})
    all_cast = sorted({c for cast in df["Cast"].dropna() for c in cast})
    all_directors = sorted(df["Director"].dropna().unique())

    with st.sidebar:
        st.markdown("## 🔍 Filters")
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
    return filtered_df
