"""
Weather Overview page - combines weather data table, line charts, and plots.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# --- Project imports setup ---
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.ui.sidebar_controls import sidebar_controls
from src.app_state import get_weather, DEFAULT_WEATHER_VARS
from src.analysis.plots import plot_weather

# --- Sidebar controls ---
price_area, city, lat, lon, year, month = sidebar_controls()

# --- Page title ---
st.title("Weather Overview")
st.info(f"Weather data for {city} ({price_area})")

# --- Tabs for different views ---
tab_plot, tab_data = st.tabs(["Plot", "Data"])

# --- Prepare date range ---
if month == "ALL":
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
else:
    start_date = f"{year}-{month}-01"
    end_date = (pd.Timestamp(start_date) + pd.offsets.MonthEnd(1)).strftime("%Y-%m-%d")

# --- Fetch weather data ---
try:
    df = get_weather(price_area, start_date, end_date, variables=DEFAULT_WEATHER_VARS)
    df = df.reset_index().rename(columns={"index": "time"})
    df["time"] = pd.to_datetime(df["time"])
except Exception as e:
    st.error(f"Could not load weather data: {e}")
    st.stop()

if df.empty:
    st.warning("No weather data available for the selected period.")
    st.stop()


# ==============================================================================
# TAB 1: Plot View
# ==============================================================================
with tab_plot:
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
    df["month_str"] = df["time"].dt.strftime("%m")

    selected_year = int(year)
    selected_month = month

    if selected_month == "ALL":
        data = df[df["time"].dt.year == selected_year].reset_index(drop=True)
    elif selected_month not in df["month_str"].unique():
        st.warning(f"No data found for month {selected_month} in {selected_year}.")
        data = pd.DataFrame()
    else:
        data = df[
            (df["time"].dt.year == selected_year) & (df["month_str"] == selected_month)
        ].reset_index(drop=True)

    # --- Normalization mode ---
    mode = st.radio(
        "View mode", ["Auto-axes", "Normalize (common scale)"], horizontal=True
    )
    method = None
    if mode.startswith("Normalize"):
        method = st.selectbox(
            "Normalization method", ["Z-score", "Min–max (0–1)", "Index 100 at start"]
        )

    # --- Plot ---
    if not data.empty:
        fig = plot_weather(data, cols, selected_month, mode, method)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data to display for the selected filters.")

    # --- Footer ---
    st.caption(
        "**Tip:** Select *Normalize* to compare variable shapes on a single scale. "
        "In *Auto-axes*, temperature, wind, precipitation, and wind direction each get their own axes."
    )


# ==============================================================================
# TAB 2: Data View
# ==============================================================================
with tab_data:
    st.subheader(f"Raw Weather Data for {city} ({price_area}) — {year}-{month}")
    st.dataframe(df.head(100), use_container_width=True)

    # --- Line Chart Table View ---
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
                help="Hourly values for the selected period",
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
