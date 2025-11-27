import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import statsmodels.api as sm
import numpy as np
from datetime import datetime
from pathlib import Path
import sys

# ---------------------------------------------------------
# Project imports
# ---------------------------------------------------------
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.db.mongo_elhub import load_production_silver, load_consumption_silver
from src.forecast.sarimax_utils import (
    prepare_data,
    fit_sarimax,
    run_forecast,
)

st.title("SARIMAX Energy Forecasting")

# ---------------------------------------------------------
# Dataset selection
# ---------------------------------------------------------
data_source = st.radio(
    "Select dataset",
    ["Production", "Consumption"],
    horizontal=True
)

with st.spinner("Setting up page… Loading energy data…"):
    df = load_production_silver() if data_source == "Production" else load_consumption_silver()

# Detect datetime column
time_col = None
for col in df.columns:
    if col.lower() in ["starttime", "timestamp", "time", "datetime"]:
        time_col = col
        break

if time_col is None:
    st.error("No valid datetime column found for time index.")
    st.stop()

# Convert and set index
df[time_col] = pd.to_datetime(df[time_col])
df = df.set_index(time_col).sort_index()

# ---- Split numeric / categorical
numeric_df = df.select_dtypes(include="number")
other_df   = df.select_dtypes(exclude="number")

# ---- Fix duplicates ONCE
numeric_df = numeric_df.groupby(numeric_df.index).sum()
other_df   = other_df.groupby(other_df.index).first()

# ---- Recombine
df = pd.concat([numeric_df, other_df], axis=1).sort_index()

# ---- Resample hourly
numeric_df = numeric_df.resample("H").mean().interpolate()
other_df   = other_df.resample("H").ffill()

df = pd.concat([numeric_df, other_df], axis=1)


# ---------------------------------------------------------
# Forecast target fixed
# ---------------------------------------------------------
target = "quantitykwh"
if target not in df.columns:
    st.error("Error: 'quantitykwh' not found.")
    st.stop()

st.markdown(f"**Forecast target:** `{target}`")


# ---------------------------------------------------------
# Exogenous variables
# ---------------------------------------------------------
invalid_exog = {"starttime", "endtime", "timestamp", "time", "group", "pricearea"}
valid_exog = [c for c in df.columns if c not in invalid_exog and c != target]

exog_cols = st.multiselect("Select exogenous variables (optional)", valid_exog)


# ---------------------------------------------------------
# ACF / PACF Diagnostics
# ---------------------------------------------------------
st.subheader("ACF / PACF Diagnostics (Plotly)")

# Compute acf/pacf values
acf_vals = sm.tsa.acf(df[target], nlags=200, fft=True)
pacf_vals = sm.tsa.pacf(df[target], nlags=200, method="ywm")

lags = np.arange(len(acf_vals))

# -----------------------------
# Plotly ACF
# -----------------------------
acf_fig = go.Figure()
acf_fig.add_trace(go.Bar(x=lags, y=acf_vals, marker_color="rgba(0,150,255,0.7)"))
acf_fig.update_layout(
    title="Autocorrelation (ACF)",
    xaxis_title="Lag",
    yaxis_title="ACF",
    height=350,
    showlegend=False
)
st.plotly_chart(acf_fig, use_container_width=True)

# -----------------------------
# Plotly PACF
# -----------------------------
pacf_fig = go.Figure()
pacf_fig.add_trace(go.Bar(x=lags, y=pacf_vals, marker_color="#000080"))
pacf_fig.update_layout(
    title="Partial Autocorrelation (PACF)",
    xaxis_title="Lag",
    yaxis_title="PACF",
    height=350,
    showlegend=False
)
st.plotly_chart(pacf_fig, use_container_width=True)

# ---------------------------------------------------------
# Timeframe
# ---------------------------------------------------------
min_date = df.index.min().date()
max_date = df.index.max().date()

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Training start", min_date, min_value=min_date, max_value=max_date)
with col2:
    end_date = st.date_input("Training end", max_date, min_value=min_date, max_value=max_date)

forecast_horizon = st.number_input("Forecast horizon (hours)", 24, 24*14, 168)


# ---------------------------------------------------------
# SARIMAX parameters
# ---------------------------------------------------------
st.subheader("SARIMAX Parameters")

p  = st.number_input("p (AR order)", 0, 12, 1)
d  = st.number_input("d (Differencing order)", 0, 2, 0)
q  = st.number_input("q (MA order)", 0, 12, 1)

sp = st.number_input("P (seasonal AR order)", 0, 12, 1)
sd = st.number_input("D (seasonal differencing order)", 0, 2, 1)
sq = st.number_input("Q (seasonal MA order)", 0, 12, 1)
m  = st.number_input("m (Season length)", 1, 365, 168)

order = (p, d, q)
seasonal_order = (sp, sd, sq, m)


# ---------------------------------------------------------
# Run Forecast
# ---------------------------------------------------------
if st.button("Run Forecast"):

    if start_date >= end_date:
        st.error("Training start must be before training end.")
        st.stop()

    st.write("Preparing data…")
    y, X = prepare_data(df, target, str(start_date), str(end_date), exog_cols)

    st.write("Fitting model…")
    st.subheader("Forecast Results")
    model = fit_sarimax(y, X, order, seasonal_order)

    # Build future exog
    if exog_cols:
        future_index = pd.date_range(start=end_date, periods=forecast_horizon + 1, freq="H")[1:]
        last_vals = df[exog_cols].iloc[-1]
        X_future = pd.DataFrame([last_vals] * forecast_horizon, index=future_index)
    else:
        X_future = None

    model_params = (model, order, seasonal_order, y, X)
    forecast, lower, upper = run_forecast(model_params, steps=forecast_horizon, X_future=X_future)

    # ---------------------------------------------------------
    # Combined plot: historical, one-step, dynamic
    # ---------------------------------------------------------
    fig = go.Figure()

    # Historical
    fig.add_trace(go.Scatter(x=y.index, y=y, mode="lines", name="Historical"))

    # One-step-ahead in-sample
    pred_insample = model.get_prediction(start=y.index[0], end=y.index[-1], dynamic=False)
    pred_insample_mean = pred_insample.predicted_mean

    fig.add_trace(go.Scatter(
        x=pred_insample_mean.index,
        y=pred_insample_mean,
        mode="lines",
        name="One-step ahead",
        line=dict(dash="dash")
    ))

    # Dynamic forecast
    fig.add_trace(go.Scatter(x=forecast.index, y=forecast, mode="lines", name="Dynamic Forecast"))

    # Confidence intervals
    fig.add_trace(go.Scatter(
        x=forecast.index.tolist() + forecast.index[::-1].tolist(),
        y=upper.tolist() + lower[::-1].tolist(),
        fill="toself",
        fillcolor="rgba(0,150,255,0.2)",
        line=dict(color="rgba(255,255,255,0)"),
        name="Confidence Interval",
    ))

    st.plotly_chart(fig, use_container_width=True)

# Model summary
    st.subheader("Model Summary")
    st.text(model.summary().as_text()) 