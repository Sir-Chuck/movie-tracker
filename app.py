import pandas as pd
import streamlit as st
from datetime import datetime
from tmdb_api import search_movie, get_best_match, get_movie_details
import os

# Load or create CSV
DATA_PATH = "data/final_movie_data.csv"
if os.path.exists(DATA_PATH):
    df = pd.read_csv(DATA_PATH)
else:
    df = pd.DataFrame(columns=[
        "title", "release_year", "genres", "runtime", "overview",
        "director", "cast", "tmdb_id", "date_added"
    ])

st.title("🎬 Movie Tracker")

# -- ADD MOVIES --
st.header("➕ Add Movies")
titles_input = st.text_area("Enter movie titles (one per line)")
if st.button("Search & Add"):
    to_add, skipped, not_found = [], [], []
    input_titles = [t.strip() for t in titles_input.strip().split("\n") if t.strip()]

    for title in input_titles:
        if title.lower() in df['title'].str.lower().values:
            skipped.append(title)
            continue

        results = search_movie(title)
        match, score = get_best_match(title, results)

        if match and score > 75:
            movie_data = get_movie_details(match["id"])
            director = ""
            cast = []
            for p in movie_data.get("credits", {}).get("crew", []):
                if p["job"] == "Director":
                    director = p["name"]
                    break
            for a in movie_data.get("credits", {}).get("cast", [])[:5]:
                cast.append(a["name"])

            new_row = {
                "title": movie_data.get("title", ""),
                "release_year": movie_data.get("release_date", "")[:4],
                "genres": ", ".join([g["name"] for g in movie_data.get("genres", [])]),
                "runtime": movie_data.get("runtime"),
                "overview": movie_data.get("overview", ""),
                "director": director,
                "cast": ", ".join(cast),
                "tmdb_id": movie_data.get("id"),
                "date_added": datetime.today().strftime("%Y-%m-%d")
            }
            to_add.append(new_row)
        elif results:
            # Let user preview what was found
            preview = [r["title"] for r in results[:3]]
            st.warning(f"No strong match for '{title}'. Top results: {preview}")
            not_found.append(title)
        else:
            not_found.append(title)

    if to_add:
        df = pd.concat([df, pd.DataFrame(to_add)], ignore_index=True)
        df.to_csv(DATA_PATH, index=False)
        st.success(f"✅ Added {len(to_add)} new movie(s).")

    if skipped:
        st.info(f"⏭ Skipped (already tracked): {', '.join(skipped)}")
    if not_found:
        st.error(f"❌ No match found: {', '.join(not_found)}")

# -- VIEW DATA --
st.header("📊 Tracked Movies")
st.dataframe(df.sort_values(by="date_added", ascending=False))
