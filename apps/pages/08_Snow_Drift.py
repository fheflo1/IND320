import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import sys

# ---------------------------------------------------------
# Project imports
# ---------------------------------------------------------
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))
from src.api.meteo_api import fetch_meteo_data  # your API wrapper


# --- Helper: compute SWE from hourly data ---
def compute_SWE(df):
    """Snow Water Equivalent: precipitation when T < 1°C."""
    return df.apply(
        lambda row: row["precipitation"] if row["temperature_2m"] < 1 else 0, axis=1
    )


# --- Tabler functions ---
def compute_Qupot(ws, dt=3600):
    return np.sum((ws**3.8) * dt) / 233_847


def compute_sector_index(direction):
    return int(((direction + 11.25) % 360) // 22.5)


def compute_sector_transport(ws, wd, dt=3600):
    sectors = [0.0] * 16
    for u, d in zip(ws, wd):
        idx = compute_sector_index(d)
        sectors[idx] += (u**3.8 * dt) / 233_847
    return sectors


def compute_snow_transport(T, F, theta, SWE, ws):
    Qupot = compute_Qupot(ws)
    Qspot = 0.5 * T * SWE
    Srwe = theta * SWE

    if Qupot > Qspot:
        Qinf = 0.5 * T * Srwe
    else:
        Qinf = Qupot

    Qt = Qinf * (1 - 0.14 ** (F / T))
    return Qt, Qupot, Qspot, Srwe


# =============================
# STREAMLIT PAGE
# =============================
st.title("Snow Drift Calculation & Visualization")

# --- Get selected map coordinates ---
if "clicked_lat" not in st.session_state or st.session_state.clicked_lat is None:
    st.error("No coordinate selected on the map! Go to Map & Selectors first.")
    st.stop()

lat = st.session_state.clicked_lat
lon = st.session_state.clicked_lon


st.success(f"Using coordinates: **{lat:.4f}, {lon:.4f}**")

# --- User selects year range ---
years = list(range(1980, datetime.now().year))
start_year, end_year = st.select_slider(
    "Select Snow-Year Range", options=years, value=(2010, 2015)
)

# Snow-year = July 1 start_year → June 30 end_year
start_date = f"{start_year}-07-01"
end_date = f"{end_year+1}-06-30"

st.info(f"Fetching ERA5 data for {start_date} → {end_date}")


# --- Fetch data ---
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

    # df already has 'time' as index → restore as column
    df = df.reset_index().rename(columns={"index": "time"})
    df["time"] = pd.to_datetime(df["time"])

    return df


df = get_meteo_data(lat, lon, start_date, end_date)

df["SWE"] = compute_SWE(df)
df["season"] = df["time"].apply(lambda t: t.year if t.month >= 7 else t.year - 1)

# --- Compute snow drift per year ---
T = 3000
F = 30000
theta = 0.5

records = []
for season, g in df.groupby("season"):
    SWE = g["SWE"].sum()
    ws = g["windspeed_10m"].values

    Qt, Qupot, Qspot, Srwe = compute_snow_transport(T, F, theta, SWE, ws)
    records.append({"season": season, "Qt_kgm": Qt})

yearly = pd.DataFrame(records)
st.subheader("📊 Annual Snow Drift")
st.dataframe(yearly)

# --- Plot Snow Drift ---
fig = px.bar(
    yearly,
    x="season",
    y="Qt_kgm",
    title="Annual Snow Drift (kg/m)",
    labels={"Qt_kgm": "Snow Drift (kg/m)"},
)
st.plotly_chart(fig, use_container_width=True)

# --- Compute wind rose ---
avg_sectors = np.zeros(16)
for season, g in df.groupby("season"):
    ws = g["windspeed_10m"].values
    wd = g["winddirection_10m"].values
    avg_sectors += compute_sector_transport(ws, wd)

avg_sectors /= len(df["season"].unique())

directions = [
    "N",
    "NNE",
    "NE",
    "ENE",
    "E",
    "ESE",
    "SE",
    "SSE",
    "S",
    "SSW",
    "SW",
    "WSW",
    "W",
    "WNW",
    "NW",
    "NNW",
]

rose = go.Figure(
    go.Barpolar(
        theta=directions,
        r=avg_sectors,
        marker_color=avg_sectors,
        marker_colorscale="turbo",  # different options: Viridis, Cividis, Plasma, Hot, Electric, Magma, Inferno, Turbo, Rainbow, Portland
    )
)
rose.update_layout(
    width=1000,
    height=700,
    margin=dict(l=40, r=40, t=80, b=40),
)

rose.update_layout(
    title="Wind Rose – Snow Drift Contribution",
    polar=dict(angularaxis=dict(direction="clockwise")),
)

st.plotly_chart(rose, use_container_width=True)
