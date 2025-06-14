import streamlit as st
import pandas as pd
from datetime import datetime
from tmdb_api import search_movie, get_movie_details, get_best_match

# Load existing movie list
try:
    df = pd.read_csv("final_movie_data.csv")
except FileNotFoundError:
    df = pd.DataFrame()

st.title("🎬 My Movie Tracker")

st.subheader("📋 Tracked Movies")
if df.empty:
    st.info("No movies tracked yet.")
else:
    st.dataframe(df, use_container_width=True)

# Section for adding new movies
st.subheader("➕ Add Multiple Movies")

movie_list_input = st.text_area(
    "Enter movie titles (comma or newline separated)",
    placeholder="Heat, The Insider, Collateral"
)

if st.button("Add Movies"):
    if not movie_list_input.strip():
        st.warning("Please enter at least one title.")
    else:
        titles = [t.strip() for t in movie_list_input.replace("\n", ",").split(",") if t.strip()]
        existing_titles = df["title_input"].str.lower().tolist() if "title_input" in df else []

        added, duplicates, not_found = [], [], []

        for title in titles:
            title_clean = title.strip()
            title_key = title_clean.lower()

            if title_key in existing_titles:
                duplicates.append(title_clean)
                continue

            results = search_movie(title_clean)
            match = get_best_match(title_clean, results)

            if match:
                details = get_movie_details(match["id"])

                new_movie = {
                    "title": details.get("title", ""),
                    "year": details.get("release_date", "")[:4],
                    "runningTimeInMinutes": details.get("runtime", None),
                    "rating": details.get("vote_average", None),
                    "ratingCount": details.get("vote_count", None),
                    "metaScore": None,
                    "reviewCount": None,
                    "userScore": None,
                    "userRatingCount": None,
                    "genre_list": [genre["name"] for genre in details.get("genres", [])],
                    "budget": details.get("budget", None),
                    "world_wide_gross": details.get("revenue", None),
                    "title_input": title_key,
                    "movie_id": details.get("id", ""),
                    "inf_index": None,
                    "adjusted_budget": None,
                    "adjusted_box_office": None,
                    "net_diff": None,
                    "final_score": None,
                    "date_added": datetime.today().strftime('%Y-%m-%d')
                }

                new_row = pd.DataFrame([new_movie])
                df = pd.concat([df, new_row], ignore_index=True)
                added.append(title_clean)
                existing_titles.append(title_key)
            else:
                not_found.append(title_clean)

        # Save and summarize
        df.to_csv("final_movie_data.csv", index=False)

        if added:
            st.success(f"✅ Added {len(added)}: {', '.join(added)}")
        if duplicates:
            st.info(f"🔁 Already tracked: {', '.join(duplicates)}")
        if not_found:
            st.error(f"❌ Not found: {', '.join(not_found)}")

# Download option
if not df.empty:
    st.download_button(
        "⬇️ Download Updated CSV",
        df.to_csv(index=False),
        "movie_data.csv",
        "text/csv"
    )
