from pathlib import Path
import sys
import pandas as pd
import streamlit as st

# --- Project imports setup ---
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.api.meteo_api import fetch_meteo_data
from src.analysis.plots import plot_weather
from src.ui.sidebar_controls import sidebar_controls

# Use the top sidebar_controls only
price_area, city, lat, lon, year, month = sidebar_controls()

# --- Price area → city mapping (kept for reference if needed) ---
PRICE_AREA_COORDS = {
    "NO1": ("Oslo", 59.91, 10.75),
    "NO2": ("Kristiansand", 58.15, 8.00),
    "NO3": ("Trondheim", 63.43, 10.39),
    "NO4": ("Tromsø", 69.65, 18.96),
    "NO5": ("Bergen", 60.39, 5.32),
}

# --- Page title ---
st.title("🌦️ Weather Plots")

start_date = f"{year}-01-01"
end_date = f"{year}-12-31"

# --- Cached data fetch ---
@st.cache_data(ttl=3600, show_spinner="Fetching weather data from Open-Meteo...")
def get_meteo_data(lat, lon, start, end):
    """Fetch and cache weather data for given coordinates."""
    df = fetch_meteo_data(
        lat,
        lon,
        start,
        end,
        [
            "temperature_2m",
            "precipitation",
            "windspeed_10m",
            "windgusts_10m",
            "winddirection_10m",
        ],
    )
    df = df.reset_index().rename(columns={"index": "time"})
    df["time"] = pd.to_datetime(df["time"])
    return df


# --- Get data ---
df = get_meteo_data(lat, lon, start_date, end_date)

# --- Page header ---
st.subheader(f"Weather Data for {city} ({price_area}) – {year}")

numeric_cols = df.select_dtypes(include="number").columns.tolist()

# Initialize session state if not present
if "selected_cols" not in st.session_state:
    st.session_state["selected_cols"] = numeric_cols.copy()

# Button to select all columns
if st.button("Select all columns"):
    st.session_state["selected_cols"] = numeric_cols.copy()

# Multiselect that can freely add/remove
selected = st.multiselect(
    "Select columns to display",
    options=numeric_cols,
    default=st.session_state["selected_cols"],
    key="selected_cols",
)

cols = selected or numeric_cols

# --- Month filtering ---
df["month"] = df["time"].dt.to_period("M").astype(str)
months = sorted(df["month"].unique())
# Use the month returned by sidebar_controls() as the default value
month_sel = st.select_slider("Select month", options=months, value=month if month in months else months[0])
data = df[df["month"] == month_sel].reset_index(drop=True)

# --- Normalization mode ---
mode = st.radio("View mode", ["Auto-axes", "Normalize (common scale)"], horizontal=True)
method = None
if mode.startswith("Normalize"):
    method = st.selectbox(
        "Normalization method", ["Z-score", "Min–max (0–1)", "Index 100 at start"]
    )

# --- Plot ---
fig = plot_weather(data, cols, month_sel, mode, method)
st.plotly_chart(fig, use_container_width=True)

# --- Footer ---
st.caption(
    "💡 **Tip:** Select *Normalize* to compare variable shapes on a single scale. "
    "In *Auto-axes*, temperature, wind, precipitation, and wind direction each get their own axes."
)
