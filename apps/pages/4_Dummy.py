import sys
from pathlib import Path

# legg til prosjektroten (en mappe opp fra apps/) i sys.path
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

import streamlit as st
from src.data import load_csv
from src.plots import plot_diverging_line


st.title("Dummy Page")

df = load_csv()
col_choice = st.selectbox(
    "Velg kolonne", options=[c for c in df.columns if c != "time"]
)
fig = plot_diverging_line(df, col=col_choice)
st.pyplot(fig)
