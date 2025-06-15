import streamlit as st
import pandas as pd
from datetime import datetime
from tmdb_api import fetch_movie_data
from backend import load_data, save_data
import os

def top_100_tab():
    st.subheader("📥 Upload Your Top 100 Movies")

    uploaded_file = st.file_uploader("Upload CSV with 'Rank' and 'Title' columns", type="csv")
    if uploaded_file:
        df_uploaded = pd.read_csv(uploaded_file)
        if "Rank" not in df_uploaded.columns or "Title" not in df_uploaded.columns:
            st.error("CSV must contain 'Rank' and 'Title' columns.")
            return

        with st.spinner("Fetching metadata..."):
            existing_df = load_data()
            existing_titles = existing_df["Title"].tolist()

            movie_data = []
            skipped = []
            not_found = []

            progress_bar = st.progress(0)
            for i, row in df_uploaded.iterrows():
                title = row["Title"]
                if title in existing_titles:
                    skipped.append(title)
                    progress_bar.progress((i + 1) / len(df_uploaded))
                    continue

                data = fetch_movie_data(title)
                if data:
                    data["Rank"] = row["Rank"]
                    data["Date Added"] = datetime.now().strftime("%Y-%m-%d")
                    movie_data.append(data)
                else:
                    not_found.append(title)
                progress_bar.progress((i + 1) / len(df_uploaded))

            if movie_data:
                non_ranked_df = existing_df[existing_df["Rank"].isna()]
                df_new = pd.DataFrame(movie_data)
                updated_df = pd.concat([non_ranked_df, df_new], ignore_index=True)
                save_data(updated_df)
                st.success(f"✅ Added {len(movie_data)} movies.")
            else:
                st.info("No new movies were added.")

            if skipped:
                st.warning(f"⚠️ Skipped (already in dataset): {', '.join(skipped)}")
            if not_found:
                st.error(f"❌ Not found: {', '.join(not_found)}")

    st.subheader("🎬 Current Top 100")
    df = load_data()
    df_top100 = df.dropna(subset=["Rank"]).sort_values("Rank")
    if not df_top100.empty:
        new_order = st.data_editor(df_top100[["Rank", "Title"]], use_container_width=True, num_rows="dynamic")
        if st.button("Save Ranking"):
            df_updated = df.copy()
            for _, row in new_order.iterrows():
                df_updated.loc[df_updated["Title"] == row["Title"], "Rank"] = row["Rank"]
            save_data(df_updated)
            st.success("✅ Ranking updated!")

    # Clear only Top 100 entries
    if st.button("❌ Clear Top 100 Data"):
        df = load_data()
        df = df[df["Rank"].isna()]  # Keep only unranked movies
        save_data(df)
        st.success("Top 100 movie data cleared.")
