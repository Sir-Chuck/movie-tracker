# top_100_tab.py

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from tmdb_api import fetch_movie_data
from backend import load_data, save_data, BACKEND_PATH

def top_100_tab():
    st.subheader("📥 Upload Your Top 100 Movies")

    uploaded_file = st.file_uploader("Upload CSV with 'Rank' and 'Title' columns", type="csv")
    if uploaded_file:
        df_uploaded = pd.read_csv(uploaded_file)
        if "Rank" not in df_uploaded.columns or "Title" not in df_uploaded.columns:
            st.error("CSV must contain 'Rank' and 'Title' columns.")
            return

        with st.spinner("Fetching movie metadata..."):
            progress_bar = st.progress(0)
            movie_data = []
            for i, row in df_uploaded.iterrows():
                data = fetch_movie_data(row["Title"])
                if data:
                    data["Rank"] = row["Rank"]
                    data["Date Added"] = datetime.now().strftime("%Y-%m-%d")
                    movie_data.append(data)
                progress_bar.progress((i + 1) / len(df_uploaded))

            if movie_data:
                existing_df = load_data()
                # Remove existing Top 100 movies
                non_ranked_df = existing_df[existing_df["Rank"].isna()] if "Rank" in existing_df.columns else existing_df
                df_new = pd.DataFrame(movie_data)
                updated_df = pd.concat([non_ranked_df, df_new], ignore_index=True)
                save_data(updated_df)
                st.success("Top 100 movies added successfully!")

    st.subheader("🎬 Current Top 100")
    df = load_data()
    df_top100 = df.dropna(subset=["Rank"]).sort_values("Rank")

    if not df_top100.empty:
        edited_df = st.data_editor(
            df_top100[["Rank", "Title"]].sort_values("Rank"),
            use_container_width=True,
            num_rows="dynamic",
            key="top100_editor"
        )
        if st.button("💾 Save Updated Rankings"):
            for _, row in edited_df.iterrows():
                df.loc[df["Title"] == row["Title"], "Rank"] = row["Rank"]
            save_data(df)
            st.success("Ranking updated!")

    if st.button("🗑️ Clear Top 100 Data"):
        df = load_data()
        df["Rank"] = None
        save_data(df)
        st.success("Top 100 rankings cleared.")
