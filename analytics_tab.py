# analytics_tab.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import altair as alt
import ast

def analytics_tab(df):
    st.markdown("## Analytics")

    if df.empty:
        st.warning("No data to analyze. Please add movies in the Data Management tab.")
        return

    # --- Safe parsing for Genre and Cast ---
    df["Genre"] = df["Genre"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
    df["Cast"] = df["Cast"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)

    # --- Numeric conversions ---
    for col in ["Box Office", "Budget", "Box Office (Adj)", "Budget (Adj)"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace("[$,]", "", regex=True), errors="coerce")

    # --- Clean ratings ---
    df["IMDB Rating"] = pd.to_numeric(df["IMDB Rating"], errors="coerce")
    df["Metacritic Score"] = pd.to_numeric(df["Metacritic Score"], errors="coerce")
    df["Rotten Percent"] = df["Rotten Tomatoes"].str.replace("%", "", regex=False)
    df["Rotten Percent"] = pd.to_numeric(df["Rotten Percent"], errors="coerce")

    # --- Flatten genres and cast for summary grouping ---
    genre_rows = []
    for _, row in df.iterrows():
        for genre in row["Genre"]:
            genre_rows.append({**row, "Single Genre": genre})
    genre_df = pd.DataFrame(genre_rows)

    cast_rows = []
    for _, row in df.iterrows():
        for actor in row["Cast"]:
            cast_rows.append({**row, "Single Actor": actor})
    cast_df = pd.DataFrame(cast_rows)

    # --- Sidebar filters (shown only on analytics tab) ---
    with st.container():
        st.sidebar.markdown("### Filter Options")
        year_range = st.sidebar.slider("Year Range", int(df["Year"].min()), int(df["Year"].max()), (int(df["Year"].min()), int(df["Year"].max())))
        genre_filter = st.sidebar.multiselect("Genres", sorted({g for sublist in df["Genre"] for g in sublist}))
        director_filter = st.sidebar.multiselect("Director", sorted(df["Director"].dropna().unique()))
        actor_filter = st.sidebar.multiselect("Actor", sorted(cast_df["Single Actor"].dropna().unique()))
        budget_range = st.sidebar.slider("Budget (Adj)", 0, int(df["Budget (Adj)"].max()), (0, int(df["Budget (Adj)"].max())))
        box_office_range = st.sidebar.slider("Box Office (Adj)", 0, int(df["Box Office (Adj)"].max()), (0, int(df["Box Office (Adj)"].max())))

    # --- Apply filters ---
    df_filtered = df.copy()
    df_filtered = df_filtered[
        (df_filtered["Year"].between(*year_range)) &
        (df_filtered["Budget (Adj)"].between(*budget_range)) &
        (df_filtered["Box Office (Adj)"].between(*box_office_range))
    ]
    if genre_filter:
        df_filtered = df_filtered[df_filtered["Genre"].apply(lambda x: any(g in x for g in genre_filter))]
    if director_filter:
        df_filtered = df_filtered[df_filtered["Director"].isin(director_filter)]
    if actor_filter:
        df_filtered = df_filtered[df_filtered["Cast"].apply(lambda x: any(a in x for a in actor_filter))]

    st.markdown("### Rating Distribution")
    rating_choice = st.selectbox("Select Rating Source", ["IMDB Rating", "Metacritic Score", "Rotten Percent"])
    fig, ax = plt.subplots()
    ax.hist(df_filtered[rating_choice].dropna(), bins=10, color="#2e0854", edgecolor="white")
    ax.set_title(f"{rating_choice} Distribution")
    st.pyplot(fig)

    st.markdown("### Rating Scatterplot")
    scatter_data = df_filtered.dropna(subset=["IMDB Rating", "Rotten Percent", "Metacritic Score"])
    scatter = alt.Chart(scatter_data).mark_circle().encode(
        x=alt.X("IMDB Rating", scale=alt.Scale(zero=False)),
        y=alt.Y("Rotten Percent", scale=alt.Scale(zero=False)),
        size="Metacritic Score",
        color="Metacritic Score",
        tooltip=["Title", "Year", "Director", "IMDB Rating", "Rotten Percent", "Metacritic Score"]
    ).properties(height=400)
    st.altair_chart(scatter, use_container_width=True)

    st.markdown("### Top 10 Summary Table")
    group_by_choice = st.selectbox("Group by", ["Year", "Single Genre", "Single Actor", "Director"])
    group_df = cast_df if group_by_choice == "Single Actor" else genre_df if group_by_choice == "Single Genre" else df_filtered
    top_summary = group_df.groupby(group_by_choice).agg({
        "Title": "count",
        "IMDB Rating": "mean",
        "Rotten Percent": "mean",
        "Metacritic Score": "mean",
        "Box Office (Adj)": "sum",
        "Budget (Adj)": "mean"
    }).rename(columns={"Title": "Movie Count"}).sort_values("Movie Count", ascending=False).head(10)
    top_summary["IMDB Rating"] = top_summary["IMDB Rating"].round(2)
    top_summary["Rotten Percent"] = top_summary["Rotten Percent"].round(2)
    top_summary["Metacritic Score"] = top_summary["Metacritic Score"].round(2)
    top_summary["Box Office (Adj)"] = top_summary["Box Office (Adj)"].map("${:,.2f}".format)
    top_summary["Budget (Adj)"] = top_summary["Budget (Adj)"].map("${:,.2f}".format)
    st.dataframe(top_summary, use_container_width=True)

    st.markdown("### Box Office vs Budget")
    bubble = alt.Chart(df_filtered.dropna(subset=["Box Office", "Budget", "IMDB Rating", "Rotten Percent"])).mark_circle().encode(
        x="Budget",
        y="Box Office",
        size="Rotten Percent",
        color="IMDB Rating",
        tooltip=["Title", "Box Office", "Budget", "IMDB Rating", "Rotten Percent"]
    ).interactive()
    st.altair_chart(bubble, use_container_width=True)

    st.markdown("### Movies Over Time (Dual Axis)")
    df_years = df_filtered.groupby("Year").agg({
        "Title": "count",
        rating_choice: "mean"
    }).rename(columns={"Title": "Movie Count"}).reset_index()
    base = alt.Chart(df_years).encode(x=alt.X("Year:O", axis=alt.Axis(labelAngle=0)))
    bars = base.mark_bar(color="#f27802").encode(y="Movie Count")
    line = base.mark_line(color="#2e0854").encode(y=alt.Y(f"{rating_choice}:Q", axis=alt.Axis(title=f"Avg {rating_choice}")))
    st.altair_chart(bars + line, use_container_width=True)

