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

# --- Sidebar (shared across app) ---
price_area, city, lat, lon, year, month = sidebar_controls()

# --- Page title ---
st.title("Production Analyses (Elhub)")
st.caption("Analyze production data by STL decomposition and frequency spectrum.")

# --- Load data from session_state ---
df = st.session_state.get("production")
if df is None or df.empty:
    st.error(
        "Production data not available. Please check that the app has been initialized."
    )
    st.stop()

df = df.copy()
df["starttime"] = pd.to_datetime(df["starttime"])
# Map 'group' to 'productiongroup' for backward compatibility
if "productiongroup" not in df.columns and "group" in df.columns:
    df["productiongroup"] = df["group"]
if "month" not in df.columns:
    df["month"] = df["starttime"].dt.strftime("%m")

# --- Filter by sidebar selections ---
filtered = df[df["pricearea"] == price_area].copy()
if month != "ALL":
    filtered = filtered[filtered["month"] == month]

groups = filtered["productiongroup"].unique()
CATEGORY_ORDER = {"productiongroup": ["hydro", "thermal", "wind", "solar", "other"]}

# Sort groups according to CATEGORY_ORDER, putting unknown groups at the end
ordered_groups = [g for g in CATEGORY_ORDER["productiongroup"] if g in groups] + [
    g for g in groups if g not in CATEGORY_ORDER["productiongroup"]
]

# --- Tabs for analyses ---
tab1, tab2 = st.tabs(["STL Analysis", "Spectrogram"])

# -------------------------------------------------------------------
# TAB 1: STL ANALYSIS
# -------------------------------------------------------------------
with tab1:
    st.subheader("STL Decomposition Analysis")

    prod_group = st.selectbox("Select Production Group", ordered_groups)

    # --- STL Parameter Controls ---
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
            help="Number of observations per seasonal period. Must be odd and less than trend.",
        )

    subset = (
        filtered[filtered["productiongroup"] == prod_group]
        .sort_values("starttime")
        .reset_index(drop=True)
    )

    if subset.empty:
        st.warning("No data found for this selection.")
    else:
        # Placeholder function – adapt if your function name differs
        fig = plot_stl_decomposition(subset, seasonal, trend)
        st.plotly_chart(fig, use_container_width=True)

        # Optional summary metrics
        st.markdown("#### Summary Statistics")
        st.dataframe(
            subset.describe(),
            use_container_width=True,
        )

# -------------------------------------------------------------------
# TAB 2: SPECTROGRAM
# -------------------------------------------------------------------
with tab2:
    st.subheader("Spectrogram Analysis")

    prod_group = st.selectbox("Select Production Group", groups, key="spec_group")

    window = st.slider("Window Length", 24, 720, 168)
    overlap = st.slider("Overlap (%)", 0, 90, 50)

    subset = (
        filtered[filtered["productiongroup"] == prod_group]
        .sort_values("starttime")
        .reset_index(drop=True)
    )

    if subset.empty:
        st.warning("No data found for this selection.")
    else:
        fig = plot_spectrogram(subset, window=window, overlap=overlap)
        st.plotly_chart(fig, use_container_width=True)

        # Optional download button
        csv = subset.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Spectrogram Data (CSV)",
            csv,
            f"spectrogram_{price_area}_{prod_group}_{year}.csv",
            "text/csv",
        )

# --- Footer ---
st.caption(
    """
    Data from **Elhub Production (Silver)** — visualized via decomposition and spectral analysis.
    Uses shared sidebar controls for location and period.
    """
)
