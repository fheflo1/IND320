from pathlib import Path
import pandas as pd
import streamlit as st

st.title("📄 DataTable")

@st.cache_data
def load_data() -> pd.DataFrame:
    # `pages/` → repo-rot er én mappe opp
    project_root = Path().cwd().parent
    data_file = project_root / "data" / "open-meteo-subset.csv"

    df = pd.read_csv(data_file)
    return df

df = load_data()
st.subheader("Rådata (første 100 rader)")
st.dataframe(df.head(100), use_container_width=True)

st.caption("Data lastet fra `data/open-meteo-subset.csv` med caching for fart.")
