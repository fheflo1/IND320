import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# --- Project imports setup ---
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.ui.sidebar_controls import sidebar_controls
from src.analysis.plots import plot_stl_decomposition, plot_spectrogram


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    # Load shared sidebar controls (returns 6 values)
    price_area, city, lat, lon, year, month = sidebar_controls()

    # Add energy-type selector HERE in the sidebar
    energy_type = st.radio(
        "Energy Type",
        ["Production", "Consumption"],
        index=0,  # Production default
        horizontal=False,
    )


# =========================================================
# LOAD DATASET BASED ON ENERGY TYPE
# =========================================================
if energy_type == "Production":
    df = st.session_state.get("production")
    group_col = "productiongroup"
    page_title = "Production Analyses (Elhub)"
else:
    df = st.session_state.get("consumption")
    group_col = "consumptiongroup"
    page_title = "Consumption Analyses (Elhub)"


# =========================================================
# PAGE TITLE
# =========================================================
st.title(page_title)
st.caption("Analyze data using STL decomposition and frequency spectrum.")


# =========================================================
# VALIDATE DATA
# =========================================================
if df is None or df.empty:
    st.error(f"{energy_type} data not available. Please initialize the app.")
    st.stop()

df = df.copy()
df["starttime"] = pd.to_datetime(df["starttime"])

# Backwards compatibility with "group"
if group_col not in df.columns and "group" in df.columns:
    df[group_col] = df["group"]

# Add month if missing
if "month" not in df.columns:
    df["month"] = df["starttime"].dt.strftime("%m")


# =========================================================
# FILTERING
# =========================================================
filtered = df[df["pricearea"] == price_area].copy()

if month != "ALL":
    filtered = filtered[filtered["month"] == month]

groups = filtered[group_col].unique()

CATEGORY_ORDER = {
    "productiongroup": ["hydro", "thermal", "wind", "solar", "other"],
    "consumptiongroup": ["residential", "commercial", "industrial", "other"],
}

order = CATEGORY_ORDER.get(group_col, [])
ordered_groups = [g for g in order if g in groups] + [
    g for g in groups if g not in order
]


# =========================================================
# TABS
# =========================================================
tab1, tab2 = st.tabs(["STL Analysis", "Spectrogram"])


# =========================================================
# TAB 1 — STL ANALYSIS
# =========================================================
with tab1:
    st.subheader(f"STL Decomposition ({energy_type})")

    energy_group = st.selectbox("Select Group", ordered_groups)

    # --- STL Parameters ---
    st.markdown("**STL Parameters**")
    col1, col2 = st.columns(2)

    with col2:
        trend = st.number_input(
            "Trend Window",
            min_value=3,
            max_value=365,
            value=169,
            step=2,
            help="Larger values give smoother trend.",
        )

    with col1:
        seasonal = st.number_input(
            "Seasonal Period",
            min_value=3,
            max_value=min(trend - 1, 179),
            value=25,
            step=2,
            help="Observations per seasonal period. Must be odd and < trend.",
        )

    subset = (
        filtered[filtered[group_col] == energy_group]
        .sort_values("starttime")
        .reset_index(drop=True)
    )

    if subset.empty:
        st.warning("No data found for this selection.")
    else:
        fig = plot_stl_decomposition(subset, seasonal, trend)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### Summary Statistics")
        st.dataframe(subset.describe(), use_container_width=True)


# =========================================================
# TAB 2 — SPECTROGRAM
# =========================================================
with tab2:
    st.subheader(f"Spectrogram ({energy_type})")

    energy_group = st.selectbox("Select Group", groups, key="spec_group")

    window = st.slider("Window Length", 24, 720, 168)
    overlap = st.slider("Overlap (%)", 0, 90, 50)

    subset = (
        filtered[filtered[group_col] == energy_group]
        .sort_values("starttime")
        .reset_index(drop=True)
    )

    if subset.empty:
        st.warning("No data available.")
    else:
        fig = plot_spectrogram(subset, window=window, overlap=overlap)
        st.plotly_chart(fig, use_container_width=True)

        csv = subset.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Spectrogram Data (CSV)",
            csv,
            f"spectrogram_{price_area}_{energy_group}_{year}.csv",
            "text/csv",
        )


# =========================================================
# FOOTER
# =========================================================
st.caption(
    f"Data from Elhub Silver Layer — {energy_type.lower()} data visualized via STL and spectral analysis."
)
