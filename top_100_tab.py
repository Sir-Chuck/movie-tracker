import streamlit as st
import pandas as pd
import os
from datetime import datetime
from tmdb_api import fetch_movie_data
from backend import load_data, save_data

def top_100_tab():
    st.subheader("📥 Upload Your Top 100 Movies")

    uploaded_file = st.file_uploader("Upload CSV with 'Rank' and 'Title' columns", type="csv")
    if uploaded_file:
        df_uploaded = pd.read_csv(uploaded_file)
        if "Rank" not in df_uploaded.columns or "Title" not in df_uploaded.columns:
            st.error("CSV must contain 'Rank' and 'Title' columns.")
            return

        with st.spinner("Fetching metadata for uploaded movies..."):
            progress = st.progress(0)
            movie_data = []
            for i, row in df_uploaded.iterrows():
                data = fetch_movie_data(row["Title"])
                if data:
                    data["Rank"] = row["Rank"]
                    data["Date Added"] = datetime.now().strftime("%Y-%m-%d")
                    movie_data.append(data)
                progress.progress((i + 1) / len(df_uploaded))

        if movie_data:
            existing_df = load_data()
            non_ranked_df = existing_df[existing_df["Rank"].isna()]
            df_new = pd.DataFrame(movie_data)
            updated_df = pd.concat([non_ranked_df, df_new], ignore_index=True)
            save_data(updated_df)
            st.success("✅ Top 100 movies added with full metadata!")

    st.subheader("🎬 Current Top 100")
    df = load_data()
    df_top100 = df.dropna(subset=["Rank"]).copy()
    df_top100["Rank"] = pd.to_numeric(df_top100["Rank"], errors="coerce")
    df_top100 = df_top100.sort_values("Rank").reset_index(drop=True)

    if not df_top100.empty:
        edited = st.data_editor(
            df_top100[["Rank", "Title"]],
            use_container_width=True,
            num_rows="dynamic",
            column_order=["Rank", "Title"],
            hide_index=True,
            key="top100_editor"
        )

        if st.button("💾 Save Ranking"):
            df_updated = df.copy()
            for _, row in edited.iterrows():
                df_updated.loc[df_updated["Title"] == row["Title"], "Rank"] = row["Rank"]
            save_data(df_updated)
            st.success("🏆 Rankings updated!")

    if st.button("🗑️ Clear Top 100 Data"):
        df = load_data()
        df_cleaned = df[df["Rank"].isna()].copy()
        save_data(df_cleaned)
        st.success("Top 100 data cleared!")
