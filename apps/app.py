import sys
from pathlib import Path
import streamlit as st

# --- Project root setup ---
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.app_state import init_app_state

st.set_page_config(page_title="IND320 Dashboard", layout="wide")

# --- Initialize app state with spinner ---
with st.spinner("Loading data and preloading datasets..."):
    init_app_state()

# --- Navigation configuration ---
NAVIGATION = {
    "Home": ["pages/01_Home_Data_Overview.py"],
    "Data Selection": ["pages/Map_and_Selectors.py"],
    "Energy": [
        "pages/02_Energy_Production.py",
        "pages/03_Production_STL_and_Spectrogram.py",
        "pages/Forecast_SARIMAX.py",
        "pages/Sliding_Window_Correlation.py",
    ],
    "Weather": [
        "pages/04_Weather_Overview.py",
        "pages/06_Meteo_Analyses.py",
        "pages/Snow_Drift.py",
    ],
    "Forecasting": ["pages/Forecast_SARIMAX.py"],
}


# --- Helper to extract page name from path ---
def page_label(path):
    name = Path(path).stem
    # Remove leading number prefixes like "01_", "02_", etc.
    if name[:2].isdigit() and name[2] == "_":
        name = name[3:]
    return name.replace("_", " ")


# --- Session state defaults ---
if "nav_section" not in st.session_state:
    st.session_state.nav_section = list(NAVIGATION.keys())[0]

if "nav_page" not in st.session_state:
    st.session_state.nav_page = NAVIGATION[st.session_state.nav_section][0]


# --- Sidebar navigation ---
st.sidebar.header("Navigation")

section = st.sidebar.selectbox(
    "Section",
    list(NAVIGATION.keys()),
    index=list(NAVIGATION.keys()).index(st.session_state.nav_section),
    key="nav_section",
)

pages = NAVIGATION[section]
page_labels = [page_label(p) for p in pages]

# Update page if section changed
if st.session_state.nav_page not in pages:
    st.session_state.nav_page = pages[0]

selected_label = st.sidebar.radio(
    "Page",
    page_labels,
    index=pages.index(st.session_state.nav_page) if st.session_state.nav_page in pages else 0,
)

# Update session state with selected page path
selected_page = pages[page_labels.index(selected_label)]
if selected_page != st.session_state.nav_page:
    st.session_state.nav_page = selected_page
    st.switch_page(selected_page)


# --- Main content ---
st.title("IND320 — Data to Decisions Dashboard")
st.markdown("<div style='height: 25px'></div>", unsafe_allow_html=True)
st.info(
    """
    This dashboard presents energy production and meteorological analyses 
    for the IND320 course.  
    Use the sidebar navigation to explore each section.
    """
)
