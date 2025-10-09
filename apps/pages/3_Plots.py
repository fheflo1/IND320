from pathlib import Path
import sys

project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

import streamlit as st
from src.data import load_csv
from src.analysis.plots import plot_weather

st.title("📈 Plots")

df = load_csv()

# brukerinput
all_cols = [c for c in df.columns if c != "time"]
select_all = st.checkbox("Select all columns", value=False)
selected = st.multiselect(
    "Select columns", options=all_cols, default=(all_cols if select_all else [])
)
cols = selected or all_cols

df["month"] = df["time"].dt.to_period("M").astype(str)
months = sorted(df["month"].unique())
month_sel = st.select_slider("Select month", options=months, value=months[0])
data = df[df["month"] == month_sel].reset_index(drop=True)

mode = st.radio("View", ["Auto-axes", "Normalize (common scale)"], horizontal=True)
method = None
if mode.startswith("Normalize"):
    method = st.selectbox("Method", ["Z-score", "Min–max (0–1)", "Index 100 at start"])

# plot
fig = plot_weather(data, cols, month_sel, mode, method)
st.pyplot(fig)

st.caption(
    "Select *Normalize* manually when you want to compare shapes on a single scale. "
    "In *Auto-axes*, temperature, wind, precipitation and wind direction get their own axes."
)
