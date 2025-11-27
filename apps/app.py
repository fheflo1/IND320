import sys
from pathlib import Path
import streamlit as st
from streamlit_option_menu import option_menu

# --- Project root setup ---
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.app_state import init_app_state

st.set_page_config(page_title="IND320 Dashboard", layout="wide")

# --- Initialize app state ---
with st.spinner("Loading data and preloading datasets..."):
    init_app_state()

# -------------------------------------------------------------
# Prevent navigation on first load
# -------------------------------------------------------------
if "nav_initialized" not in st.session_state:
    st.session_state.nav_initialized = False

# -------------------------------------------------------------
# Page map (single source of truth)
# -------------------------------------------------------------
PAGE_MAP = {
    "Energy": {
        "Data Overview": "pages/01_Home_Data_Overview.py",
        "Energy Production": "pages/02_Energy_Production.py",
        "Production STL & Spectrogram": "pages/03_Production_STL_and_Spectrogram.py",
    },
    "Weather": {
        "Weather Overview": "pages/04_Weather_Overview.py",
        "Meteo Analyses": "pages/05_Meteo_Analyses.py",
        "Snow Drift": "pages/08_Snow_Drift.py",
    },
    "Forecasting": {
        "Forecast SARIMAX": "pages/07_Forecast_SARIMAX.py",
    },
    "Data Selection": {
        "Map & Selectors": "pages/09_Map_and_Selectors.py",
    },
}

# -------------------------------------------------------------
# Sidebar Navigation
# -------------------------------------------------------------
with st.sidebar:

    selected_energy = option_menu(
        "Energy",
        options=list(PAGE_MAP["Energy"].keys()),
        default_index=0,
        key="energy_menu",
    )

    selected_weather = option_menu(
        "Weather",
        options=list(PAGE_MAP["Weather"].keys()),
        default_index=0,
        key="weather_menu",
    )

    selected_forecasting = option_menu(
        "Forecasting",
        options=list(PAGE_MAP["Forecasting"].keys()),
        default_index=0,
        key="forecast_menu",
    )

    selected_map = option_menu(
        "Data Selection",
        options=list(PAGE_MAP["Data Selection"].keys()),
        default_index=0,
        key="map_menu",
    )

# -------------------------------------------------------------
# Navigation Logic — only active AFTER first interaction
# -------------------------------------------------------------

# Trigger navigation only after initialization is complete
if st.session_state.nav_initialized:

    if selected_energy in PAGE_MAP["Energy"]:
        st.switch_page(PAGE_MAP["Energy"][selected_energy])

    elif selected_weather in PAGE_MAP["Weather"]:
        st.switch_page(PAGE_MAP["Weather"][selected_weather])

    elif selected_forecasting in PAGE_MAP["Forecasting"]:
        st.switch_page(PAGE_MAP["Forecasting"][selected_forecasting])

    elif selected_map in PAGE_MAP["Data Selection"]:
        st.switch_page(PAGE_MAP["Data Selection"][selected_map])

# Mark navigation as initialized AFTER first render
st.session_state.nav_initialized = True

# -------------------------------------------------------------
# Home page (root page content)
# -------------------------------------------------------------
st.title("IND320 — Data to Decisions Dashboard")
st.markdown("<div style='height: 25px'></div>", unsafe_allow_html=True)

st.info(
    """
    This dashboard presents energy production and meteorological analyses 
    for the IND320 course.  
    Use the sidebar navigation to explore each section.
    """
)
