import streamlit as st
import pandas as pd
from datetime import datetime
from tmdb_api import fetch_movie_data
from backend import load_data, save_data
import os

BACKEND_PATH = "data/backend_movie_data.csv"

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

            # Remove all currently ranked movies
            non_ranked_df = existing_df[existing_df["Rank"].isna()] if "Rank" in existing_df.columns else existing_df

            df_new = pd.DataFrame(movie_data)
            updated_df = pd.concat([non_ranked_df, df_new], ignore_index=True)
            save_data(updated_df)
            st.success("✅ Top 100 movies added successfully!")

    st.subheader("🎬 Current Top 100")

    df = load_data()
    if "Rank" in df.columns:
        df_top100 = df[df["Rank"].notna()].copy()
        df_top100["Rank"] = pd.to_numeric(df_top100["Rank"], errors="coerce")
        df_top100 = df_top100.sort_values("Rank")

        display_cols = [
            "Rank", "Title", "Year", "Genre", "Director", "Cast",
            "IMDB Rating", "Rotten Tomatoes", "Metacritic Score",
            "Box Office", "Budget", "Date Added"
        ]
        display_cols = [col for col in display_cols if col in df_top100.columns]

        if not df_top100.empty:
            st.caption("⬆️ Drag rows to reorder your rankings. Edit Rank or Title if needed.")
            new_order = st.data_editor(
                df_top100[display_cols],
                use_container_width=True,
                num_rows="dynamic",
                key="top100_editor"
            )

            if st.button("💾 Save Updated Rankings"):
                df_updated = df.copy()
                for _, row in new_order.iterrows():
                    df_updated.loc[df_updated["Title"] == row["Title"], "Rank"] = row["Rank"]
                save_data(df_updated)
                st.success("✅ Rankings updated!")

    if st.button("🗑️ Clear All Top 100 Data"):
        df = load_data()
        if "Rank" in df.columns:
            df = df[df["Rank"].isna()]  # Keep only unranked entries
        save_data(df)
        st.success("✅ Top 100 data cleared.")
