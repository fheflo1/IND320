import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import sys
import time

# ---------------------------------------------------------
# Project imports
# ---------------------------------------------------------
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.api.meteo_api import fetch_meteo_data
from src.db.mongo_elhub import load_production_silver, load_consumption_silver


# ---------------------------------------------------------
# PRICEAREA → default coordinates for auto meteo
# ---------------------------------------------------------
PRICEAREA_COORDS = {
    "NO1": (59.9139, 10.7522),
    "NO2": (58.1467, 7.9956),
    "NO3": (63.4305, 10.3951),
    "NO4": (69.6492, 18.9553),
    "NO5": (60.39299, 5.32415),
}

# ---------------------------------------------------------
# Page
# ---------------------------------------------------------
st.title("🔄 Sliding Window Correlation — Meteorology vs Energy")

st.write(
    "This tool computes a **sliding window correlation** between hourly meteorology "
    "and hourly energy (production or consumption). It supports:\n"
    "• **Manual window inspection** (slider)\n"
    "• **Autoplay animation** of the sliding window\n"
    "• Three-panel visualization (meteo → energy → correlation)"
)


# ---------------------------------------------------------
# Sidebar inputs
# ---------------------------------------------------------
st.sidebar.header("Correlation Settings")

energy_type = st.sidebar.radio("Energy Type:", ["Production", "Consumption"])

df_energy_raw = load_production_silver() if energy_type == "Production" else load_consumption_silver()

priceareas = sorted(df_energy_raw["pricearea"].dropna().unique())
pricearea_choice = st.sidebar.selectbox("Price Area:", priceareas)

df_energy_raw = df_energy_raw[df_energy_raw["pricearea"] == pricearea_choice]

group_col = "group"
groups = sorted(df_energy_raw[group_col].dropna().unique())
group_choice = st.sidebar.selectbox("Energy Group:", groups)

valid_years = sorted(df_energy_raw["starttime"].dropna().dt.year.unique())
start_year, end_year = st.sidebar.select_slider(
    "Select analysis range (years)",
    options=valid_years,
    value=(valid_years[0], valid_years[-1]),
)
start_date = f"{start_year}-01-01"
end_date = f"{end_year}-12-31"

meteo_vars = ["temperature_2m", "precipitation", "windspeed_10m", "windgusts_10m", "winddirection_10m"]
meteo_choice = st.sidebar.selectbox("Meteorological variable:", meteo_vars)

lag = st.sidebar.slider("Lag (hours):", -240, 240, 0)
window = st.sidebar.slider("Rolling window (hours):", 6, 240, 48)


# ---------------------------------------------------------
# Fetch METEO
# ---------------------------------------------------------
lat, lon = PRICEAREA_COORDS[pricearea_choice]
st.success(f"Using METEO location for {pricearea_choice}: lat={lat:.4f}, lon={lon:.4f}")

@st.cache_data(ttl=1800)
def get_meteo(lat, lon, start, end):
    df = fetch_meteo_data(
        lat, lon, start, end,
        ["temperature_2m","precipitation","windspeed_10m","windgusts_10m","winddirection_10m"]
    )
    df = df.reset_index().rename(columns={"index": "time"})
    df["time"] = pd.to_datetime(df["time"]).dt.tz_localize(None)
    return df

df_m = get_meteo(lat, lon, start_date, end_date)
df_m = df_m.set_index("time").sort_index()
df_m = df_m.apply(pd.to_numeric, errors="coerce").resample("1H").mean().ffill()
df_m = df_m[~df_m.index.duplicated(keep="first")]


# ---------------------------------------------------------
# Prepare energy
# ---------------------------------------------------------
df_e = df_energy_raw.copy()
df_e = df_e[df_e[group_col] == group_choice]
df_e = df_e[(df_e["starttime"] >= start_date) & (df_e["starttime"] <= end_date)]
df_e = df_e.rename(columns={"starttime": "time", "quantitykwh": "energy"})
df_e["time"] = pd.to_datetime(df_e["time"]).dt.tz_localize(None)
df_e = df_e.set_index("time")[["energy"]]
df_e = df_e.dropna().resample("1H").mean().ffill()
df_e = df_e[~df_e.index.duplicated(keep="first")]

if df_e.empty:
    st.error("No energy data for this selection.")
    st.stop()


# ---------------------------------------------------------
# Align meteo → energy
# ---------------------------------------------------------
df = pd.DataFrame({
    "meteo": df_m[meteo_choice].reindex(df_e.index, method="nearest", tolerance="1H"),
    "energy": df_e["energy"]
}).dropna()

if lag != 0:
    df["energy"] = df["energy"].shift(lag)

df = df.dropna()
times = df.index


# ---------------------------------------------------------
# Compute sliding window correlation manually
# ---------------------------------------------------------
def safe_corr_window(arr):
    if arr.ndim != 2 or arr.shape[1] != 2:
        return np.nan
    dfw = pd.DataFrame(arr, columns=["m", "e"]).dropna()
    if len(dfw) < 3:
        return np.nan
    if dfw["m"].std() == 0 or dfw["e"].std() == 0:
        return np.nan
    return dfw["m"].corr(dfw["e"])

m = df[["meteo", "energy"]].to_numpy()
corr = np.full(len(m), np.nan)
for i in range(window, len(m)):
    corr[i] = safe_corr_window(m[i-window:i])

df["corr"] = corr


# =========================================================
# SLIDING WINDOW — MANUAL WINDOW SELECTION
# =========================================================

st.subheader("🔍 Window Selection (Manual)")

# Number of correlation points (same as len(df))
num_points = len(df)

# Create a slider for selecting the window center
center = st.slider(
    "Select Window Center Position:",
    min_value=window,
    max_value=num_points - 1,
    value=num_points // 2,
    step=1
)

# Compute window boundaries
window_start = max(0, center - window)
window_end   = center
    
st.write(f"Window range: **{window_start} → {window_end}** ({window} hours)")


# =========================================================
# PLOT 1 — Meteo with window highlighted
# =========================================================
import plotly.graph_objects as go

fig1 = go.Figure()

# full line
fig1.add_trace(go.Scatter(
    x=df.index, y=df["meteo"],
    mode="lines",
    line=dict(color="blue", width=1),
    name="Meteo"
))

# highlighted window
fig1.add_trace(go.Scatter(
    x=df.index[window_start:window_end],
    y=df["meteo"].iloc[window_start:window_end],
    mode="lines",
    line=dict(color="red", width=3),
))


fig1.update_layout(
    title=f"Meteo: {meteo_choice}",
    height=400,
    showlegend=False
)


# =========================================================
# PLOT 2 — Energy with window highlighted
# =========================================================

fig2 = go.Figure()

fig2.add_trace(go.Scatter(
    x=df.index, y=df["energy"],
    mode="lines",
    line=dict(color="royalblue", width=1),
    name="Energy"
))

fig2.add_trace(go.Scatter(
    x=df.index[window_start:window_end],
    y=df["energy"].iloc[window_start:window_end],
    mode="lines",
    line=dict(color="red", width=3),
))


fig2.update_layout(
    title=f"Energy: {group_choice} ({energy_type})",
    height=400,
    showlegend=False
)


# =========================================================
# PLOT 3 — Correlation timeline with safe vertical marker
# =========================================================

fig3 = go.Figure()

fig3.add_trace(go.Scatter(
    x=df.index, y=df["corr"],
    mode="lines",
    line=dict(color="green", width=1),
    name="Correlation"
))

# safe timestamp vertical line using shape
center_ts = df.index[center]

fig3.add_shape(
    type="line",
    x0=center_ts, x1=center_ts,
    y0=float(np.nanmin(df["corr"])),
    y1=float(np.nanmax(df["corr"])),
    line=dict(color="red", width=2),
)

fig3.update_layout(
    title=f"Sliding Window Correlation (Window={window}h, Lag={lag}h)",
    height=400,
    showlegend=False
)


# =========================================================
# DISPLAY
# =========================================================

st.plotly_chart(fig1, use_container_width=True)
st.plotly_chart(fig2, use_container_width=True)
st.plotly_chart(fig3, use_container_width=True)



st.write("### Raw correlation values")
st.dataframe(df[["corr"]].dropna())
