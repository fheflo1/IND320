from pathlib import Path
import sys
import pandas as pd
import streamlit as st

# --- Project imports setup ---
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.api.meteo_api import fetch_meteo_data
from src.ui.sidebar_controls import sidebar_controls

# Use only the top sidebar_controls
price_area, city, lat, lon, year, month = sidebar_controls()

# --- Price area → city mapping (kept for reference, not used if sidebar_controls provides coords) ---
PRICE_AREA_COORDS = {
    "NO1": ("Oslo", 59.91, 10.75),
    "NO2": ("Kristiansand", 58.15, 8.00),
    "NO3": ("Trondheim", 63.43, 10.39),
    "NO4": ("Tromsø", 69.65, 18.96),
    "NO5": ("Bergen", 60.39, 5.32),
}

# --- Page title ---
st.title("📄 Weather Data Table")

start_date = f"{year}-{month}-01"
end_date = pd.Timestamp(start_date) + pd.offsets.MonthEnd(1)
end_date = end_date.strftime("%Y-%m-%d")

# --- Fetch and cache data from API ---
@st.cache_data(ttl=3600, show_spinner="Fetching weather data from Open-Meteo...")
def get_meteo_data(lat, lon, start, end):
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

# --- Load data ---
df = get_meteo_data(lat, lon, start_date, end_date)

# --- Main section ---
st.subheader(f"Raw Weather Data for {city} ({price_area}) — {year}-{month}")
st.dataframe(df.head(100), use_container_width=True)

# --- Prepare first-month-like line table ---
st.subheader(f"Line Chart View — {city}, {year}-{month}")

numeric_cols = df.select_dtypes(include="number").columns.tolist()

# Convert dataframe to "column/value list" format for display
df_rows = []
for col in numeric_cols:
    df_rows.append({"variable": col, "values": df[col].tolist()})
df_rows = pd.DataFrame(df_rows)

st.dataframe(
    df_rows,
    column_config={
        "variable": st.column_config.TextColumn("Variable", width="small"),
        "values": st.column_config.LineChartColumn(
            "Time Series (hourly)",
            help="Hourly values for the selected month",
            width="large",
        ),
    },
    hide_index=True,
    use_container_width=True,
    height=1035,
    row_height=200,
)

st.caption(
    f"Data shown for **{city} ({price_area})**, year **{year}**, month **{month}**. "
    "Includes temperature, precipitation, wind speed, gusts, and direction from the Open-Meteo API."
)
