import streamlit as st
import pandas as pd
from datetime import datetime
from tmdb_api import fetch_movie_data
import matplotlib.pyplot as plt
import altair as alt

st.set_page_config(page_title="MovieGraph", layout="wide")
st.markdown("""
<style>
    html, body, [class*="css"]  {
        font-family: Verdana;
        color: #2a2a2a;
    }
    .title {
        font-family: 'Courier New', monospace;
        font-weight: normal;
        font-size: 36px;
        margin-bottom: 0;
    }
    .subtitle {
        font-size: 18px;
        letter-spacing: 2px;
        font-weight: bold;
    }
    .subtitle span:nth-child(1) { color: #f27802; }
    .subtitle span:nth-child(2) { color: #2e0854; }
    .subtitle span:nth-child(3) { color: #7786c8; }
    .subtitle span:nth-child(4) { color: #708090; }
    .subtitle span:nth-child(5) { color: #b02711; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">MovieGraph</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle"><span>C</span><span>H</span><span>U</span><span>C</span><span>K</span></div>', unsafe_allow_html=True)

REQUIRED_COLUMNS = [
    "Title", "Year", "Genre", "Director", "Cast",
    "IMDB Rating", "Metacritic Score",
    "Runtime", "Language", "Overview",
    "Box Office", "Box Office (Adj)", "Budget", "Budget (Adj)", "Date Added"
]

def load_data():
    if "movie_data" not in st.session_state:
        st.session_state.movie_data = pd.DataFrame(columns=REQUIRED_COLUMNS)
    return st.session_state.movie_data

def save_data(df):
    st.session_state.movie_data = df

def data_management_tab():
    df = load_data()

    st.subheader("Add Movies to Your Collection")
    titles = st.text_area("Enter movie titles (one per line):")
    if st.button("Add Movies"):
        titles_list = [t.strip() for t in titles.split("\n") if t.strip()]
        added, skipped, not_found = [], [], []

        with st.spinner("Fetching movie data..."):
            for title in titles_list:
                if title in df["Title"].values:
                    skipped.append(title)
                    continue
                movie = fetch_movie_data(title)
                if movie:
                    movie["Date Added"] = datetime.now().strftime("%Y-%m-%d")
                    df = pd.concat([df, pd.DataFrame([movie])], ignore_index=True)
                    added.append(title)
                else:
                    not_found.append(title)

        save_data(df)
        st.success(f"✅ Added: {len(added)} | ⏩ Skipped: {len(skipped)} | ❌ Not Found: {len(not_found)}")
        if skipped:
            st.info("Skipped Movies: " + ", ".join(skipped))
        if not_found:
            st.warning("Not Found: " + ", ".join(not_found))

    st.subheader("Your Movie Collection")
    st.markdown(f"**Total Movies:** {len(df)}")
    st.dataframe(df[REQUIRED_COLUMNS], use_container_width=True)

    if st.button("Clear Data"):
        st.session_state.movie_data = pd.DataFrame(columns=REQUIRED_COLUMNS)
        st.success("All movie data cleared.")
        st.experimental_rerun()

def analytics_tab():
    df = load_data()
    if df.empty:
        st.info("No data to analyze. Add movies first.")
        return

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["IMDB Rating"] = pd.to_numeric(df["IMDB Rating"], errors="coerce")
    df["Metacritic Score"] = pd.to_numeric(df["Metacritic Score"], errors="coerce")
    df["Box Office (Adj)"] = pd.to_numeric(df["Box Office (Adj)"], errors="coerce")
    df["Budget (Adj)"] = pd.to_numeric(df["Budget (Adj)"], errors="coerce")

    st.subheader("Analytics")

    # Rating comparison scatter plot
    st.markdown("### IMDB vs Metacritic")
    scatter = alt.Chart(df.dropna(subset=["IMDB Rating", "Metacritic Score"])).mark_circle(size=80).encode(
        x="IMDB Rating",
        y="Metacritic Score",
        tooltip=["Title", "IMDB Rating", "Metacritic Score"]
    ).interactive()
    st.altair_chart(scatter, use_container_width=True)

    # Histogram of Metacritic
    st.markdown("### Metacritic Score Distribution")
    st.bar_chart(df["Metacritic Score"].dropna())

    # Histogram of Release Year
    st.markdown("### Release Year Distribution")
    st.bar_chart(df["Year"].dropna())

    # Box Office vs Budget scatter
    st.markdown("### Adjusted Box Office vs Budget")
    scatter2 = alt.Chart(df.dropna(subset=["Box Office (Adj)", "Budget (Adj)"])).mark_circle(size=80).encode(
        x="Budget (Adj)",
        y="Box Office (Adj)",
        tooltip=["Title", "Box Office (Adj)", "Budget (Adj)"]
    ).interactive()
    st.altair_chart(scatter2, use_container_width=True)

tabs = st.tabs(["Data Management", "Analytics"])

with tabs[0]:
    data_management_tab()

with tabs[1]:
    analytics_tab()
