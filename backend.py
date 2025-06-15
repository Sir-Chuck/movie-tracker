import pandas as pd
import os

BACKEND_PATH = "data/backend_movie_data.csv"

def load_data():
    if os.path.exists(BACKEND_PATH):
        return pd.read_csv(BACKEND_PATH)
    else:
        return pd.DataFrame()

def save_data(df):
    os.makedirs("data", exist_ok=True)
    df.to_csv(BACKEND_PATH, index=False)
