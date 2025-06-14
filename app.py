import streamlit as st
import pandas as pd
from datetime import datetime
from tmdb_api import search_movie, get_movie_details

# Load data
try:
    df = pd.read_csv("final_movie_data.csv")
except FileNotFoundError:
    df = pd.DataFrame()

st.title("🎬 My Movie Tracker")

# Display the movie table
st.subheader("Your Tracked Movies")
st.dataframe(df, use_container_width=True)

# Section to add new movies
st.subheader("➕ Add a New Movie")

movie_title = st.text_input("Enter a movie title")

if st.button("Search & Add Movie"):
    if not movie_title.strip():
        st.warning("Please enter a valid movie title.")
    else:
        results = search_movie(movie_title)
        if results:
            selected = results[0]
            details = get_movie_details(selected["id"])

            # Build the new movie record
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
                "title_input": movie_title.lower(),
                "movie_id": details.get("id", ""),
                "inf_index": None,
                "adjusted_budget": None,
                "adjusted_box_office": None,
                "net_diff": None,
                "final_score": None,
                "date_added": datetime.today().strftime('%Y-%m-%d')
            }

            # Convert to DataFrame row and append
            new_row = pd.DataFrame([new_movie])
            df = pd.concat([df, new_row], ignore_index=True)

            st.success(f"✅ Added '{new_movie['title']}' ({new_movie['year']})")

            # Optionally save file (or comment out for now)
            df.to_csv("final_movie_data.csv", index=False)
        else:
            st.error("No movie found with that title.")

# Optional download button
st.download_button("⬇️ Download Updated CSV", df.to_csv(index=False), "movie_data.csv", "text/csv")
