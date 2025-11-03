import sys
from pathlib import Path

# legg til prosjektroten (en mappe opp fra apps/) i sys.path
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

import streamlit as st
from src.data.load_data import load_csv
from src.analysis.plots import plot_diverging_line
from src.ui.sidebar_controls import sidebar_controls

price_area, city, lat, lon, year, month = sidebar_controls()


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

if df is not None and not df.empty:
    col_choice = st.selectbox(
        "Select column", options=[c for c in df.columns if c != "time"]
    )

    fig = cached_plot(df, col_choice)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No data loaded. Please check your data source.")
