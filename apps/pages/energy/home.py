import streamlit as st
import pandas as pd
import re
from pathlib import Path
import sys
from calendar import month_name

# --- Project imports setup ---
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.ui.navigation import render_navigation
from src.ui.sidebar_controls import sidebar_controls
from src.app_state import get_weather, PRICEAREAS, DEFAULT_WEATHER_VARS

# --- Render navigation sidebar ---
render_navigation()

# --- Shared sidebar ---
price_area, city, lat, lon, year, month = sidebar_controls()

st.title("Home — Data Overview")
st.info("Use the sidebar to explore weather and energy data across different analyses.")


# ----------------------------------------------------------
# Utility
# ----------------------------------------------------------
_unit_re = re.compile(r"\(([^)]+)\)")


# ----------------------------------------------------------
# Prepare date range for current sidebar selection
# ----------------------------------------------------------
start_date = f"{year}-{month}-01"
end_date = (pd.Timestamp(start_date) + pd.offsets.MonthEnd(1)).strftime("%Y-%m-%d")

# ----------------------------------------------------------
# Load datasets
# ----------------------------------------------------------
# Meteo - use get_weather from app_state
try:
    meteo_df = get_weather(
        price_area, start_date, end_date, variables=DEFAULT_WEATHER_VARS
    )
    meteo_df = meteo_df.reset_index().rename(columns={"index": "time"})
    meteo_df["time"] = pd.to_datetime(meteo_df["time"])
    if not meteo_df.empty:
        meteo_daily = meteo_df.groupby(meteo_df["time"].dt.date).mean(numeric_only=True)
    else:
        meteo_daily = pd.DataFrame()
except Exception as e:
    st.warning(f"Could not load weather data: {e}")
    meteo_df = pd.DataFrame()
    meteo_daily = pd.DataFrame()

# Elhub - use session_state
elhub_df = st.session_state.get("production")
if elhub_df is None or elhub_df.empty:
    st.error(
        "Production data not available. Please check that the app has been initialized."
    )
    st.stop()

elhub_df = elhub_df.copy()
elhub_df["starttime"] = pd.to_datetime(elhub_df["starttime"])
if "month" not in elhub_df.columns:
    elhub_df["month"] = elhub_df["starttime"].dt.month
# Map 'group' back to 'productiongroup' if needed for compatibility
if "productiongroup" not in elhub_df.columns and "group" in elhub_df.columns:
    elhub_df["productiongroup"] = elhub_df["group"]

# --- Filter based on sidebar selections ---
filtered = elhub_df[elhub_df["pricearea"] == price_area]
filtered = filtered[filtered["starttime"].dt.year == int(year)]

# --- Handle ALL vs single month ---
if month != "ALL":
    filtered = filtered[filtered["month"] == int(month)]

# ----------------------------------------------------------
# Layout
# ----------------------------------------------------------
st.subheader(f"Overview for {city} ({price_area}) — {year}-{month}")

col_weather, col_energy = st.columns(2)

# ==========================================================
# WEATHER OVERVIEW
# ==========================================================
with col_weather:
    st.markdown("### Open-Meteo Overview")

    if meteo_daily.empty:
        st.warning("No weather data available for the selected year and month.")
    else:
        avg_row = meteo_daily.mean()
        numeric_cols = [
            c for c in avg_row.index if pd.api.types.is_numeric_dtype(avg_row[c])
        ]

        st.markdown(f"**Average daily values for {month_name[int(month)]}**")
        cols = st.columns(min(3, len(numeric_cols)))

        for i, col_name in enumerate(numeric_cols):
            val = avg_row[col_name]
            display = "-" if pd.isna(val) else f"{val:.1f}"
            m = _unit_re.search(col_name)
            if m:
                display += f" {m.group(1)}"
            label = _unit_re.sub("", col_name).strip()
            cols[i % 3].metric(label, display)

# ----------------------------------------------------------
# ENERGY OVERVIEW
# ----------------------------------------------------------
with col_energy:
    st.markdown("### Elhub Production Overview")

    if filtered.empty:
        available_years = sorted(elhub_df["starttime"].dt.year.unique())
        st.warning(
            f"No Elhub production data for {year}. "
            f"Available years: {', '.join(map(str, available_years))}."
        )
    else:
        # --- Aggregation ---
        if month == "ALL":
            monthly_totals = filtered.groupby("month")["quantitykwh"].sum().sort_index()

            st.markdown(f"**Total production by month in {year} ({price_area})**")
            st.bar_chart(monthly_totals)

            total_year = monthly_totals.sum()
            st.metric(
                label=f"Total annual production ({price_area})",
                value=f"{total_year:,.0f} kWh",
            )

        else:
            total_energy = filtered["quantitykwh"].sum()
            st.metric(
                f"Total production in {month_name[int(month)]} ({price_area})",
                f"{total_energy:,.0f} kWh",
            )

            if "productiongroup" in filtered.columns:
                grouped = (
                    filtered.groupby("productiongroup")["quantitykwh"]
                    .sum()
                    .sort_values(ascending=False)
                )
                st.bar_chart(grouped)
# ==========================================================
# SUMMARY
# ==========================================================
st.divider()
st.markdown("### Summary")

summary_cols = st.columns(2)
with summary_cols[0]:
    if not meteo_df.empty:
        st.write(
            "**Weather data range:**",
            f"{meteo_df['time'].min().date()} → {meteo_df['time'].max().date()}",
        )
        st.write("**Records:**", len(meteo_df))
        st.write("**Columns:**", ", ".join(meteo_df.columns))
    else:
        st.write("No weather data loaded.")

with summary_cols[1]:
    if not elhub_df.empty:
        st.write(
            "**Elhub data range:**",
            f"{elhub_df['starttime'].min().date()} → {elhub_df['starttime'].max().date()}",
        )
        st.write("**Records:**", len(elhub_df))
        if "productiongroup" in elhub_df.columns:
            st.write(
                "**Production groups:**",
                ", ".join(sorted(elhub_df["productiongroup"].unique())),
            )
    else:
        st.write("No Elhub data loaded.")

st.caption(
    "Tip: Use the sidebar to change year, area, or month — both datasets update automatically."
)
