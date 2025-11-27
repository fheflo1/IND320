import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path
import sys

# --- Project imports setup ---
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.app_state import init_app_state
from src.analysis.anomaly_detection import (
    detect_temperature_outliers,
    detect_precipitation_anomalies,
)
from src.ui.sidebar_controls import sidebar_controls
from src.api.meteo_api import fetch_meteo_data

# Initialize app state (preload data if not already loaded)
init_app_state()


st.title("Meteo Analyses (Open-Meteo)")

price_area, city, lat, lon, year, month = sidebar_controls()


# --- Fetch weather data ---
@st.cache_data(ttl=3600)
def get_weather(lat, lon, start, end):
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


start_date, end_date = f"{year}-01-01", f"{year}-12-31"
df = get_weather(lat, lon, start_date, end_date)

# --- Tabs for analysis types ---
tab1, tab2 = st.tabs(["Outlier Detection (SPC)", "Anomaly Detection (LOF)"])

# ============================================================
# 🔹 TAB 1 — SPC Temperature Outliers
# ============================================================
with tab1:
    st.subheader("Temperature Outlier Detection (SPC)")

    cutoff = st.slider("Frequency Cutoff (DCT)", 0.01, 0.5, 0.05, step=0.01)
    std_thresh = st.slider("STD Threshold", 1.0, 5.0, 3.0, step=0.5)

    try:
        result = detect_temperature_outliers(df, cutoff, std_thresh)

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=result["time"],
                y=result["temperature"],
                mode="lines",
                name="Temperature",
                line=dict(color="#4c78a8"),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=result["time"],
                y=result["smoothed"],
                mode="lines",
                name="Smoothed",
                line=dict(color="#f58518"),
            )
        )

        # Highlight outliers
        fig.add_trace(
            go.Scatter(
                x=result.loc[result["outlier"], "time"],
                y=result.loc[result["outlier"], "temperature"],
                mode="markers",
                name="Outliers",
                marker=dict(color="red", size=6, symbol="circle"),
            )
        )

        fig.update_layout(
            title="SPC Temperature Outlier Detection",
            template="plotly_dark",
            height=500,
            legend=dict(orientation="h", y=-0.2),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Summary table
        n_out = result["outlier"].sum()
        st.write(f"**Detected outliers:** {n_out}")
        if n_out > 0:
            st.dataframe(result[result["outlier"]][["time", "temperature"]])

    except Exception as e:
        st.error(f"Error: {e}")

# ============================================================
# 🔹 TAB 2 — LOF Precipitation Anomalies
# ============================================================
with tab2:
    st.subheader("Precipitation Anomaly Detection (LOF)")

    outlier_prop = st.slider("Outlier proportion", 0.001, 0.1, 0.01, step=0.001)

    try:
        result = detect_precipitation_anomalies(df, outlier_prop)

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=result["time"],
                y=result["precipitation"],
                mode="lines",
                name="Precipitation",
                line=dict(color="#54a24b"),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=result.loc[result["anomaly"], "time"],
                y=result.loc[result["anomaly"], "precipitation"],
                mode="markers",
                name="Anomalies",
                marker=dict(color="red", size=6, symbol="x"),
            )
        )

        fig.update_layout(
            title="LOF Precipitation Anomalies",
            template="plotly_dark",
            height=500,
            legend=dict(orientation="h", y=-0.2),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Summary
        n_anom = result["anomaly"].sum()
        st.write(f"**Detected anomalies:** {n_anom}")
        if n_anom > 0:
            st.dataframe(result[result["anomaly"]][["time", "precipitation"]])

    except Exception as e:
        st.error(f"Error: {e}")
