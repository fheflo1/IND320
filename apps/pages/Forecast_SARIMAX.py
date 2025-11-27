import streamlit as st
import pandas as pd
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
    if data_source == "Production":
        df = load_production_silver()
    else:
        df = load_consumption_silver()

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

# Show duplicate count BEFORE fixing
st.write("Duplicate timestamps before:", df.index.duplicated().sum())

# --- Split numeric and categorical columns ---
numeric_df = df.select_dtypes(include="number")
other_df   = df.select_dtypes(exclude="number")

# --- Fix duplicates ONCE ---
# Numeric = sum (energy signals)
numeric_df = numeric_df.groupby(numeric_df.index).sum()

# Categorical = keep first
other_df = other_df.groupby(other_df.index).first()

# --- Recombine after duplicate fix ---
df = pd.concat([numeric_df, other_df], axis=1).sort_index()

# --- Resample to hourly ---
numeric_df = numeric_df.resample("h").mean().interpolate()
other_df   = other_df.resample("h").ffill()

df = pd.concat([numeric_df, other_df], axis=1)

# Show duplicate count AFTER fixing
st.write("Duplicate timestamps after:", df.index.duplicated().sum())


# ---------------------------------------------------------
# Forecast target = ALWAYS quantitykwh
# ---------------------------------------------------------
target = "quantitykwh"
if target not in df.columns:
    st.error("Error: The dataset does not contain 'quantitykwh'.")
    st.stop()

st.markdown(f"**Forecast target:** `{target}`")

# ---------------------------------------------------------
# Valid exogenous variables
# ---------------------------------------------------------
invalid_exog = {"starttime", "endtime", "timestamp", "time", "group", "pricearea"}
valid_exog = [
    col for col in df.columns
    if col not in invalid_exog and col != target
]

exog_cols = st.multiselect(
    "Select exogenous variables (optional)",
    valid_exog,
)

# ---------------------------------------------------------
# Timeframe selection
# ---------------------------------------------------------
with st.expander("How long will training take?"):
    st.markdown(
        """
Training time for SARIMAX depends mainly on:

### **1. Amount of training data**
Larger time windows = longer training.
- 1–3 months → **fast**
- 6–12 months → **medium**
- Several years → **slow**

SARIMAX complexity scales roughly **linearly** with number of time steps.

---

### **2. Model complexity**
Higher values of (p, d, q, P, D, Q) increase training time.

- `(1,1,1)` + `(1,1,1,24)` → **good balance of speed and accuracy**
- Parameters > 3 often give diminishing returns but add a lot of time.

---

### **3. Seasonal period (m)**
- **m = 24** (daily seasonality) → fast  
- **m = 168** (weekly seasonality) → slower  
- Very large `m` values → long estimation time

---

### **4. Exogenous variables**
Adding exogenous variables slightly increases training time.

---

### **Summary**
If the model feels slow:
- **Reduce the training window**
- **Lower p, q, P, Q**
- Keep **d and D ≤ 1**
- Use **m = 24** unless you know you need weekly seasonality

This keeps forecasting fast and stable.
        """
    )

min_date = df.index.min().date()
max_date = df.index.max().date()

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Training start", min_date, min_value=min_date, max_value=max_date)
with col2:
    end_date = st.date_input("Training end", max_date, min_value=min_date, max_value=max_date)

forecast_horizon = st.number_input("Forecast horizon (hours)", 24, 24 * 14, 168)

# ---------------------------------------------------------
# SARIMAX parameters
# ---------------------------------------------------------
st.subheader("SARIMAX Parameters")

with st.expander("What do the SARIMAX parameters mean?"):
    st.markdown(
        """
### **ARIMA (p, d, q)**
These parameters control the **time series structure**:

- **p – Autoregressive order (AR)**  
  How many previous time steps the model uses.  
  Higher `p` = longer memory.

- **d – Differencing order**  
  Number of times to difference the series to make it stationary.  
  Typical values: **0 or 1**.

- **q – Moving Average order (MA)**  
  How many past forecast errors the model uses.

---

### **Seasonal part (P, D, Q, m)**
Used when the data has repeating patterns (daily, weekly, yearly).

- **P – Seasonal AR order**  
- **D – Seasonal differencing**  
- **Q – Seasonal MA order**  
- **m – Season length**  
  Example for hourly data:  
  - Daily seasonality → **24**  
  - Weekly seasonality → **168**  

If unsure, use **m = 24** (daily seasonality).

---

### **Exogenous variables (optional)**
External factors that help explain the main series, e.g.:

- Weather (temperature, wind, solar radiation)
- Price signals
- Market indicators

Must be **known in the future** to use them in forecasting.

---

### **Tips**
- Start simple: `(p,d,q) = (1,1,1)` and `(P,D,Q,m) = (1,1,1,24)`
- If the model fails to converge, reduce parameters
- Differencing (`d` and `D`) should rarely exceed **1**
        """
    )


p = st.number_input("p (AR order)", 0, 12, 1)
d = st.number_input("d (Differencing order)", 0, 2, 0)
q = st.number_input("q (MA order)", 0, 12, 1)

sp = st.number_input("P (seasonal AR order)", 0, 12, 1)
sd = st.number_input("D (seasonal differencing order)", 0, 2, 1)
sq = st.number_input("Q (seasonal MA order)", 0, 12, 1)
m = st.number_input("m (Season length)", 1, 365, 168)

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

    y, X = prepare_data(
        df,
        target,
        str(start_date),
        str(end_date),
        exog_cols,
    )

    st.write("Fitting model… (slow – not cached)")
    model = fit_sarimax(y, X, order, seasonal_order)

    # Build future exogenous frame
    if exog_cols:
        future_index = pd.date_range(
            start=end_date,
            periods=forecast_horizon + 1,
            freq="H"
        )[1:]

        last_vals = df[exog_cols].iloc[-1]
        X_future = pd.DataFrame([last_vals] * forecast_horizon, index=future_index)
    else:
        X_future = None

    model_params = (model, order, seasonal_order, y, X)

    forecast, lower, upper = run_forecast(
        model_params=model_params,
        steps=forecast_horizon,
        X_future=X_future,
    )

    # ---------------------------------------------------------
    # Plot forecast
    # ---------------------------------------------------------
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=y.index, y=y, mode="lines", name="Historical"
    ))
    fig.add_trace(go.Scatter(
        x=forecast.index, y=forecast, mode="lines", name="Forecast"
    ))
    fig.add_trace(go.Scatter(
        x=forecast.index.tolist() + forecast.index[::-1].tolist(),
        y=upper.tolist() + lower[::-1].tolist(),
        fill="toself",
        fillcolor="rgba(0,150,255,0.2)",
        line=dict(color="rgba(255,255,255,0)"),
        name="Confidence Interval",
    ))

    st.plotly_chart(fig, use_container_width=True)
