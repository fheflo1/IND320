import sys
from pathlib import Path

# legg til prosjektroten (en mappe opp fra apps/) i sys.path
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

import streamlit as st
from src.data import load_csv
from src.analysis.plots import plot_diverging_line

st.title("Dummy Page")


# Cache the loaded dataframe for efficiency
@st.cache_data
def cached_load_csv():
    return load_csv()


# Optionally cache the plotting step as well
@st.cache_data
def cached_plot(df, col: str):
    return plot_diverging_line(df, col=col)


df = cached_load_csv()
col_choice = st.selectbox(
    "Velg kolonne", options=[c for c in df.columns if c != "time"]
)
fig = cached_plot(df, col_choice)
st.pyplot(fig)
