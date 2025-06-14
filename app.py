import streamlit as st
import pandas as pd
from datetime import datetime
import os
from tmdb_api import get_movie_data

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

DATA_PATH = "data/final_movie_data.csv"

# Load existing data
if os.path.exists(DATA_PATH):
    df = pd.read_csv(DATA_PATH)
else:
    df = pd.DataFrame()

# Page config
st.set_page_config(page_title="🎬 Movie Tracker", layout="wide")
st.title("🎬 Movie Tracker")

st.markdown("Enter movie titles (one per line or separated by commas):")

user_input = st.text_area("Add new movies", height=200)

if st.button("Add Movies"):
    if user_input.strip():
        # Handle both comma- and newline-separated inputs
        raw_titles = user_input.replace(",", "\n").splitlines()
        input_titles = [title.strip() for title in raw_titles if title.strip()]

        added = []
        skipped = []
        not_found = []
        fuzzy_matches = []

        existing_titles = set(df['title'].str.lower()) if not df.empty else set()

        for title in input_titles:
            if title.lower() in existing_titles:
                skipped.append(title)
                continue

            result = get_movie_data(title)

            if result and result.get("title"):
                result["date_added"] = datetime.now().strftime("%Y-%m-%d")
                df = pd.concat([df, pd.DataFrame([result])], ignore_index=True)
                added.append(result["title"])
            elif result and result.get("fuzzy_match"):
                not_found.append(title)
                fuzzy_matches.append((title, result["fuzzy_match"]))
            else:
                not_found.append(title)

        df.to_csv(DATA_PATH, index=False)

        # Feedback to user
        if added:
            st.success(f"✅ Added: {', '.join(added)}")
        if skipped:
            st.info(f"🔁 Already tracked: {', '.join(skipped)}")
        if not_found:
            st.warning(f"❌ Not found: {', '.join(not_found)}")
        if fuzzy_matches:
            st.markdown("### 🔎 Fuzzy Match Suggestions")
            for orig, match in fuzzy_matches:
                st.markdown(f"- **{orig}** → _{match}_")

    else:
        st.warning("Please enter at least one movie title.")

# Show current data
if not df.empty:
    st.markdown("### 🎞️ Your Tracked Movies")
    st.dataframe(df.sort_values(by="date_added", ascending=False))
