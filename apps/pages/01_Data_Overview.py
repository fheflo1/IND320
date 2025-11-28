import streamlit as st
import pandas as pd
import re
from pathlib import Path
import sys
from calendar import month_name

# --- Project imports setup ---
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.ui.sidebar_controls import sidebar_controls
from src.app_state import get_weather, DEFAULT_WEATHER_VARS


# ==========================================================
# Sidebar controls
# ==========================================================
price_area, city, lat, lon, year, month = sidebar_controls()

st.title(f"Data Overview")
st.subheader(f"Overview for {city} ({price_area}) — {year}-{month}")


# ----------------------------------------------------------
# Utility
# ----------------------------------------------------------
_unit_re = re.compile(r"\(([^)]+)\)")


# ----------------------------------------------------------
# Date handling
# ----------------------------------------------------------
if month.upper() == "ALL":
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
else:
    try:
        start_date = f"{year}-{month}-01"
        end_date = (pd.Timestamp(start_date) + pd.offsets.MonthEnd(1)).strftime("%Y-%m-%d")
    except Exception:
        start_date = f"{year}-{month}-01"
        end_date = f"{year}-{month}-28"


# ----------------------------------------------------------
# Load WEATHER
# ----------------------------------------------------------
try:
    meteo_df = get_weather(price_area, start_date, end_date, variables=DEFAULT_WEATHER_VARS)
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


# ----------------------------------------------------------
# Load PRODUCTION + CONSUMPTION
# ----------------------------------------------------------
prod_df = st.session_state.get("production")
cons_df = st.session_state.get("consumption")

if prod_df is None or prod_df.empty:
    st.error("Production data not available — check initialization.")
    st.stop()

if cons_df is None or cons_df.empty:
    st.error("Consumption data not available — check initialization.")
    st.stop()

# Normalize
prod_df = prod_df.copy()
cons_df = cons_df.copy()

prod_df["starttime"] = pd.to_datetime(prod_df["starttime"])
cons_df["starttime"] = pd.to_datetime(cons_df["starttime"])

for df in (prod_df, cons_df):
    if "month" not in df.columns:
        df["month"] = df["starttime"].dt.month

# Map legacy naming if needed
if "productiongroup" not in prod_df.columns and "group" in prod_df.columns:
    prod_df["productiongroup"] = prod_df["group"]

if "consumptiongroup" not in cons_df.columns and "group" in cons_df.columns:
    cons_df["consumptiongroup"] = cons_df["group"]

# Filter base
prod_filtered = prod_df[(prod_df["pricearea"] == price_area) &
                        (prod_df["starttime"].dt.year == int(year))]

cons_filtered = cons_df[(cons_df["pricearea"] == price_area) &
                        (cons_df["starttime"].dt.year == int(year))]

if month != "ALL":
    prod_filtered = prod_filtered[prod_filtered["month"] == int(month)]
    cons_filtered = cons_filtered[cons_filtered["month"] == int(month)]


# ==========================================================
# WEATHER — FULL WIDTH
# ==========================================================
st.markdown("## Weather Widgets")

if meteo_daily.empty:
    st.warning("No weather data available for this selection.")
else:
    avg_row = meteo_daily.mean()
    numeric_cols = [c for c in avg_row.index if pd.api.types.is_numeric_dtype(avg_row[c])]

    # Label
    if month.upper() == "ALL":
        month_label = f"{year} (all months)"
    else:
        try:
            month_label = month_name[int(month)]
        except:
            month_label = month

    st.markdown(f"**Average daily weather values — {month_label}**")

    # ----- Force all widgets in one single tight row -----
    n = len(numeric_cols)
    cols = st.columns(n, gap="small")   # gap = compact spacing

    for i, col_name in enumerate(numeric_cols):
        val = avg_row[col_name]
        display = "-" if pd.isna(val) else f"{val:.1f}"

        m = _unit_re.search(col_name)
        if m:
            display += f" {m.group(1)}"

        label = _unit_re.sub("", col_name).strip()
        cols[i].metric(label, display)


# ==========================================================
# PRODUCTION + CONSUMPTION — SIDE BY SIDE
# ==========================================================
col_left, col_right = st.columns(2)

# ---------------- PRODUCTION --------------------
with col_left:
    st.markdown("## Production")

    if prod_filtered.empty:
        st.warning("No production data for this period.")

    else:
        # ALL MONTHS
        if month == "ALL":
            monthly_totals = (
                prod_filtered.groupby("month")["quantitykwh"]
                .sum()
                .sort_index()
            )

            total_prod = monthly_totals.sum()
            st.metric("Total annual production", f"{total_prod:,.0f} kWh")  # ⬅️ MOVED ABOVE

            st.bar_chart(monthly_totals)

        # SINGLE MONTH
        else:
            grouped = (
                prod_filtered.groupby("productiongroup")["quantitykwh"]
                .sum()
                .sort_values(ascending=False)
            )

            total_prod = grouped.sum()
            st.metric(f"Total production in {month_label}", f"{total_prod:,.0f} kWh")  # ⬅️ MOVED ABOVE

            st.bar_chart(grouped)

# ---------------- CONSUMPTION --------------------
with col_right:
    st.markdown("## Consumption")

    if cons_filtered.empty:
        st.warning("No consumption data for this period.")

    else:
        # ALL MONTHS
        if month == "ALL":
            monthly_totals = (
                cons_filtered.groupby("month")["quantitykwh"]
                .sum()
                .sort_index()
            )

            total_cons = monthly_totals.sum()
            st.metric("Total annual consumption", f"{total_cons:,.0f} kWh")  # ⬅️ MOVED ABOVE

            st.bar_chart(monthly_totals)

        # SINGLE MONTH
        else:
            grouped = (
                cons_filtered.groupby("consumptiongroup")["quantitykwh"]
                .sum()
                .sort_values(ascending=False)
            )

            total_cons = grouped.sum()
            st.metric(f"Total consumption in {month_label}", f"{total_cons:,.0f} kWh")  # ⬅️ MOVED ABOVE

            st.bar_chart(grouped)



# ==========================================================
# TOTAL PRODUCTION & CONSUMPTION OVERVIEW
# ==========================================================

st.subheader("Energy Balance Overview")

# --- Load production / consumption ---
prod_df = st.session_state.get("production")
cons_df = st.session_state.get("consumption")

if prod_df is None or prod_df.empty:
    st.error("Production data missing.")
    st.stop()

if cons_df is None or cons_df.empty:
    st.error("Consumption data missing.")
    st.stop()

# --- Prepare data ---
prod_df = prod_df.copy()
cons_df = cons_df.copy()
prod_df["starttime"] = pd.to_datetime(prod_df["starttime"])
cons_df["starttime"] = pd.to_datetime(cons_df["starttime"])

prod_df["month"] = prod_df["starttime"].dt.month
cons_df["month"] = cons_df["starttime"].dt.month
prod_df["year"] = prod_df["starttime"].dt.year
cons_df["year"] = cons_df["starttime"].dt.year

# --- Filter for selected area & year ---
prod_f = prod_df[(prod_df["pricearea"] == price_area) & (prod_df["year"] == int(year))]
cons_f = cons_df[(cons_df["pricearea"] == price_area) & (cons_df["year"] == int(year))]

# --- Filter month if not ALL ---
if month != "ALL":
    m = int(month)
    prod_f = prod_f[prod_f["month"] == m]
    cons_f = cons_f[cons_f["month"] == m]

# --- Compute total balance ---
total_prod = prod_f["quantitykwh"].sum()
total_cons = cons_f["quantitykwh"].sum()
net_balance = total_prod - total_cons

# === PERIOD LABEL ===
if month == "ALL":
    period_label = f"{year} (all months)"
else:
    period_label = f"{month_name[int(month)]} {year}"

# ==========================================================
#        DELTA CALCULATION (monthly or yearly)
# ==========================================================

delta_value = None
delta_percent = None
delta_text = None

# --- A) Yearly delta (ALL mode) ---
if month == "ALL":
    prev_year = int(year) - 1

    prev_prod = prod_df[(prod_df["pricearea"] == price_area) & (prod_df["year"] == prev_year)]
    prev_cons = cons_df[(cons_df["pricearea"] == price_area) & (cons_df["year"] == prev_year)]

    if not prev_prod.empty and not prev_cons.empty:
        prev_balance = prev_prod["quantitykwh"].sum() - prev_cons["quantitykwh"].sum()

        delta_value = net_balance - prev_balance
        if prev_balance != 0:
            delta_percent = (delta_value / abs(prev_balance)) * 100

# --- B) Monthly delta (single month mode) ---
else:
    current_month = int(month)

    # If January → compare with December of previous year
    if current_month == 1:
        prev_month = 12
        prev_year = int(year) - 1
    else:
        prev_month = current_month - 1
        prev_year = int(year)

    prev_prod = prod_df[(prod_df["pricearea"] == price_area) &
                        (prod_df["year"] == prev_year) &
                        (prod_df["month"] == prev_month)]

    prev_cons = cons_df[(cons_df["pricearea"] == price_area) &
                        (cons_df["year"] == prev_year) &
                        (cons_df["month"] == prev_month)]

    if not prev_prod.empty and not prev_cons.empty:
        prev_balance = prev_prod["quantitykwh"].sum() - prev_cons["quantitykwh"].sum()

        delta_value = net_balance - prev_balance
        if prev_balance != 0:
            delta_percent = (delta_value / abs(prev_balance)) * 100


# ==========================================================
# METRIC DISPLAY
# ==========================================================

# Choose color based on sign of delta_value
if delta_value is not None:
    # Use 'normal'
    delta_color = "normal"

    if delta_percent is not None:
        # Determine whether we're comparing to last year (ALL) or last month (single month)
        if month == "ALL":
            period_suffix = "last year"
        else:
            period_suffix = "last month"
        delta_text = f"{delta_value:,.0f} kWh ({delta_percent:.1f}%) from {period_suffix}"
    else:
        delta_text = f"{delta_value:,.0f} kWh"
else:
    delta_color = "off"
    delta_text = None

c1 = st.columns(1)[0]

c1.metric(
    label=f"Net Energy Balance — {period_label}",
    value=f"{net_balance:,.0f} kWh",
    delta=delta_text,
    delta_color=delta_color,
)



# ==========================================================
# SUMMARY
# ==========================================================
st.divider()
st.markdown("## Summary")

summary_cols = st.columns(2)

with summary_cols[0]:
    st.write("### Weather Data")
    if not meteo_df.empty:
        st.write(
            f"**Range:** {meteo_df['time'].min().date()} → {meteo_df['time'].max().date()}"
        )
        st.write("**Records:**", len(meteo_df))
    else:
        st.write("No weather data loaded.")

with summary_cols[1]:
    st.write("### Energy Data")
    st.write(
        f"Production range: {prod_df['starttime'].min().date()} → {prod_df['starttime'].max().date()}"
    )
    st.write("Production records:", len(prod_df))
    st.write(
        f"Consumption range: {cons_df['starttime'].min().date()} → {cons_df['starttime'].max().date()}"
    )
    st.write("Consumption records:", len(cons_df))

st.caption("Tip: Use the sidebar to change year, area, or month — everything updates automatically.")
