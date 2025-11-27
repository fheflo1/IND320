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

# Use the shared sidebar controls
price_area, city, lat, lon, year, month = sidebar_controls()

# --- Page title ---
st.title("Weather Overview")
st.caption("Comprehensive weather data view with table and interactive visualizations.")


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


# --- Prepare date ranges ---
# For data table: use selected month
start_date_month = f"{year}-{month}-01"
end_date_month = (pd.Timestamp(start_date_month) + pd.offsets.MonthEnd(1)).strftime(
    "%Y-%m-%d"
)

# For plots: use full year
start_date_year = f"{year}-01-01"
end_date_year = f"{year}-12-31"

# --- Load data for the full year (superset) ---
df_year = get_meteo_data(lat, lon, start_date_year, end_date_year)

# Filter for the selected month
if month == "ALL":
    df_month = df_year.copy()
else:
    df_month = df_year[df_year["time"].dt.strftime("%m") == month].reset_index(
        drop=True
    )

# --- Tabs for different views ---
tab1, tab2 = st.tabs(["Data Table & Line Charts", "Interactive Plots"])

# =============================================================================
# TAB 1: Data Table & Line Charts
# =============================================================================
with tab1:
    st.subheader(f"Weather Data for {city} ({price_area}) — {year}-{month}")

    if df_month.empty:
        st.warning("No weather data available for the selected period.")
    else:
        # Raw data table (limited to 100 rows for performance)
        st.markdown("#### Raw Data")
        st.dataframe(df_month.head(100), use_container_width=True)

        # Line chart table view
        st.markdown("#### Line Chart View")
        numeric_cols = df_month.select_dtypes(include="number").columns.tolist()

        # Convert dataframe to "column/value list" format for display
        df_rows = []
        for col in numeric_cols:
            df_rows.append({"variable": col, "values": df_month[col].tolist()})
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
            height=min(1035, 200 * len(numeric_cols) + 35),
            row_height=200,
        )

    st.caption(
        f"Data shown for **{city} ({price_area})**, year **{year}**, month **{month}**. "
        "Includes temperature, precipitation, wind speed, gusts, and direction from the Open-Meteo API."
    )

# =============================================================================
# TAB 2: Interactive Plots
# =============================================================================
with tab2:
    st.subheader(f"Weather Plots for {city} ({price_area}) – {year}")

    numeric_cols = df_year.select_dtypes(include="number").columns.tolist()

    # Initialize session state if not present
    if "selected_cols" not in st.session_state:
        st.session_state["selected_cols"] = numeric_cols.copy()

    # Button to select all columns
    if st.button("Select all columns"):
        st.session_state["selected_cols"] = numeric_cols.copy()

    # Multiselect for column selection
    selected = st.multiselect(
        "Select columns to display",
        options=numeric_cols,
        default=st.session_state["selected_cols"],
        key="selected_cols",
    )

    cols = selected or numeric_cols

    # Filter data for the selected month/period
    df_plot = df_year.copy()
    df_plot["month"] = df_plot["time"].dt.strftime("%m")

    if month == "ALL":
        data = df_plot[df_plot["time"].dt.year == int(year)].reset_index(drop=True)
    elif month not in df_plot["month"].unique():
        st.warning(f"No data found for month {month} in {year}.")
        data = pd.DataFrame()
    else:
        data = df_plot[
            (df_plot["time"].dt.year == int(year)) & (df_plot["month"] == month)
        ].reset_index(drop=True)

    # Normalization mode
    mode = st.radio(
        "View mode", ["Auto-axes", "Normalize (common scale)"], horizontal=True
    )
    method = None
    if mode.startswith("Normalize"):
        method = st.selectbox(
            "Normalization method", ["Z-score", "Min–max (0–1)", "Index 100 at start"]
        )

    # Plot
    if not data.empty:
        fig = plot_weather(data, cols, month, mode, method)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available to plot.")

    st.caption(
        "**Tip:** Select *Normalize* to compare variable shapes on a single scale. "
        "In *Auto-axes*, temperature, wind, precipitation, and wind direction each get their own axes."
    )
