import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path
import sys

# ---------------------------------------------------------
# Project imports
# ---------------------------------------------------------
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.api.meteo_api import fetch_meteo_data
from src.db.mongo_elhub import load_production_silver, load_consumption_silver


# ---------------------------------------------------------
# PRICEAREA → coordinates
# ---------------------------------------------------------
PRICEAREA_COORDS = {
    "NO1": (59.9139, 10.7522),
    "NO2": (58.1467, 7.9956),
    "NO3": (63.4305, 10.3951),
    "NO4": (69.6492, 18.9553),
    "NO5": (60.39299, 5.32415),
}

PRICEAREA_CITY = {
    "NO1": "Oslo",
    "NO2": "Kristiansand",
    "NO3": "Trondheim",
    "NO4": "Tromsø",
    "NO5": "Bergen",
}


# ---------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------
st.title("Sliding Window Correlation — Meteorology vs Energy")

st.write("""
This tool computes a **sliding window correlation** between hourly meteorology and 
hourly energy (production or consumption).

Features:
- Manual sliding window inspection  
- Three stacked visualizations  
- Lag adjustment  
- Full caching & error handling  
""")


# ---------------------------------------------------------
# Caching wrappers
# ---------------------------------------------------------
@st.cache_data(ttl=1800)
def load_energy_cached(energy_type):
    return load_production_silver() if energy_type == "Production" else load_consumption_silver()


@st.cache_data(ttl=1800)
def get_meteo(lat, lon, start, end):
    df = fetch_meteo_data(
        lat, lon, start, end,
        ["temperature_2m","precipitation","windspeed_10m",
         "windgusts_10m","winddirection_10m"]
    )
    df = df.reset_index().rename(columns={"index": "time"})
    df["time"] = pd.to_datetime(df["time"]).dt.tz_localize(None)
    return df


@st.cache_data
def compute_corr_array(matrix, window):
    """Compute sliding window correlation efficiently."""
    corr = np.full(len(matrix), np.nan)
    for i in range(window, len(matrix)):
        sub = matrix[i-window:i]
        dfw = pd.DataFrame(sub, columns=["m", "e"]).dropna()
        if len(dfw) >= 3 and dfw["m"].std() > 0 and dfw["e"].std() > 0:
            corr[i] = dfw["m"].corr(dfw["e"])
    return corr


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
st.sidebar.header("Correlation Settings")

energy_type = st.sidebar.radio("Energy Type:", ["Production", "Consumption"])

df_energy_raw = load_energy_cached(energy_type)

priceareas = sorted(df_energy_raw["pricearea"].dropna().unique())
pricearea_choice = st.sidebar.selectbox("Price Area:", priceareas)

df_energy_raw = df_energy_raw[df_energy_raw["pricearea"] == pricearea_choice]

groups = sorted(df_energy_raw["group"].dropna().unique())
group_choice = st.sidebar.selectbox("Energy Group:", groups)

valid_years = sorted(df_energy_raw["starttime"].dropna().dt.year.unique())
start_year, end_year = st.sidebar.select_slider(
    "Select analysis range (years)",
    options=valid_years,
    value=(valid_years[0], valid_years[-1]),
)

start_date = f"{start_year}-01-01"
end_date   = f"{end_year}-12-31"

meteo_vars = [
    "temperature_2m", "precipitation", "windspeed_10m",
    "windgusts_10m", "winddirection_10m"
]
meteo_choice = st.sidebar.selectbox("Meteorological variable:", meteo_vars)

lag = st.sidebar.slider("Lag (hours):", -240, 240, 0)
window = st.sidebar.slider("Rolling window (hours):", 6, 240, 48)


# ---------------------------------------------------------
# FETCH METEO
# ---------------------------------------------------------
city = PRICEAREA_CITY.get(pricearea_choice, "Unknown City")
st.info(f"Using METEO data for {pricearea_choice} ({city})")

lat, lon = PRICEAREA_COORDS[pricearea_choice]
df_m = get_meteo(lat, lon, start_date, end_date)
df_m = df_m.set_index("time").sort_index()
df_m = df_m.apply(pd.to_numeric, errors="coerce").resample("1H").mean().ffill()
df_m = df_m[~df_m.index.duplicated()]


# ---------------------------------------------------------
# PREPARE ENERGY
# ---------------------------------------------------------
df_e = df_energy_raw.copy()
df_e = df_e[df_e["group"] == group_choice]
df_e = df_e[(df_e["starttime"] >= start_date) & (df_e["starttime"] <= end_date)]

if df_e.empty:
    st.error("No energy data found for this energy group & year range.")
    st.stop()

df_e = df_e.rename(columns={"starttime": "time", "quantitykwh": "energy"})
df_e["time"] = pd.to_datetime(df_e["time"]).dt.tz_localize(None)
df_e = df_e.set_index("time")["energy"].resample("1H").mean().ffill()
df_e = df_e[~df_e.index.duplicated()]


# ---------------------------------------------------------
# ALIGN METEO → ENERGY
# ---------------------------------------------------------
df = pd.DataFrame({
    "meteo": df_m[meteo_choice].reindex(df_e.index, method="nearest", tolerance="1H"),
    "energy": df_e
}).dropna()

if df.empty:
    st.error("No overlapping METEO and ENERGY timestamps were found.")
    st.stop()

# Apply lag
if lag != 0:
    df["energy"] = df["energy"].shift(lag)

df = df.dropna()

if df.empty:
    st.error("Lag removed all overlapping data. Choose a smaller lag.")
    st.stop()


# ---------------------------------------------------------
# COMPUTE CORRELATION
# ---------------------------------------------------------
matrix = df[["meteo", "energy"]].to_numpy()

if window >= len(matrix):
    st.error("Rolling window is larger than available data.")
    st.stop()

corr = compute_corr_array(matrix, window)
df["corr"] = corr

if df["corr"].dropna().empty:
    st.error("Correlation could not be computed (all windows invalid).")
    st.stop()


# ---------------------------------------------------------
# WINDOW SELECTION
# ---------------------------------------------------------
st.subheader("🔍 Window Selection (Manual)")

num_points = len(df)
center = st.slider(
    "Select Window Center Position:",
    min_value=window,
    max_value=num_points - 1,
    value=num_points // 2,
)

window_start = max(0, center - window)
window_end   = center


st.write(f"Window range: **{window_start} → {window_end}** ({window} hours)")


# ---------------------------------------------------------
# PLOT 1 — METEO
# ---------------------------------------------------------
fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=df.index, y=df["meteo"], mode="lines",
                          line=dict(color="royalblue", width=1)))

fig1.add_trace(go.Scatter(
    x=df.index[window_start:window_end],
    y=df["meteo"].iloc[window_start:window_end],
    mode="lines",
    line=dict(color="red", width=3),
))

fig1.update_layout(title=f"Meteo: {meteo_choice}", height=350, showlegend=False)


# ---------------------------------------------------------
# PLOT 2 — ENERGY
# ---------------------------------------------------------
fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=df.index, y=df["energy"], mode="lines",
                          line=dict(color="royalblue", width=1)))

fig2.add_trace(go.Scatter(
    x=df.index[window_start:window_end],
    y=df["energy"].iloc[window_start:window_end],
    mode="lines",
    line=dict(color="red", width=3),
))

fig2.update_layout(title=f"Energy: {group_choice} ({energy_type})", height=350, showlegend=False)


# ---------------------------------------------------------
# PLOT 3 — CORRELATION
# ---------------------------------------------------------
fig3 = go.Figure()
fig3.add_trace(go.Scatter(x=df.index, y=df["corr"], mode="lines",
                          line=dict(color="blue", width=1)))

center_ts = df.index[center]

# vertical marker
fig3.add_shape(
    type="line",
    x0=center_ts, x1=center_ts,
    y0=float(np.nanmin(df["corr"])),
    y1=float(np.nanmax(df["corr"])),
    line=dict(color="red", width=2),
)

fig3.update_layout(
    title=f"Sliding Window Correlation (Window={window}h, Lag={lag}h)",
    height=350,
    showlegend=False
)


# ---------------------------------------------------------
# DISPLAY PLOTS
# ---------------------------------------------------------
st.plotly_chart(fig1, use_container_width=True)
st.plotly_chart(fig2, use_container_width=True)
st.plotly_chart(fig3, use_container_width=True)

st.subheader("Raw Correlation Values")
st.dataframe(df[["corr"]].dropna())

