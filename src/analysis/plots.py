import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.tsa.seasonal import STL
from scipy.signal import spectrogram


def plot_diverging_line(df, col: str):
    pts = df[["time", col]].copy()
    pts["time"] = pd.to_datetime(pts["time"])
    pts[col] = pd.to_numeric(pts[col], errors="coerce")
    pts = pts.dropna().reset_index(drop=True)

    if pts.empty:
        return go.Figure()

    y_all = pts[col].values
    vmin, vmax = np.nanmin(y_all), np.nanmax(y_all)

    # Diverging colormap logic
    if vmin < 0 and vmax > 0:
        vmax_abs = max(abs(vmin), abs(vmax))
        cmin, cmax = -vmax_abs, vmax_abs
        colorscale = "RdBu"
    else:
        cmin, cmax = vmin, vmax
        colorscale = "Spectral"

    # Fast ScatterGL with color per point
    fig = go.Figure(
        data=go.Scattergl(
            x=pts["time"],
            y=pts[col],
            mode="lines+markers",
            line=dict(width=1.5, color="lightgray"),
            marker=dict(
                color=pts[col],
                colorscale=colorscale,
                cmin=cmin,
                cmax=cmax,
                size=3,
                colorbar=dict(title=col),
            ),
        )
    )

    fig.update_layout(
        title=f"{col} over time",
        template="plotly_dark",
        margin=dict(l=40, r=100, t=50, b=40),
        xaxis=dict(title="Time", tickformat="%Y-%m"),
        yaxis=dict(title=col),
    )

    return fig


def prepare_first_month_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes a DataFrame with a 'time' column and returns a DataFrame
    with one row per numeric column and a LineChartColumn-compatible list
    of values for the first month in the dataset.
    Returns (rows_dataframe, first_month_period).
    """

    # Convert time
    df = df.copy()
    df["time"] = pd.to_datetime(df["time"])

    # Find first month
    first_month = df["time"].dt.to_period("M").min()
    fm = df[df["time"].dt.to_period("M") == first_month].reset_index(drop=True)

    # Only numeric columns
    num_cols = fm.select_dtypes(include="number").columns.tolist()

    # Build "table" format
    rows = [
        {"column": col, "first_month": fm[col].astype(float).tolist()}
        for col in num_cols
    ]
    df_rows = pd.DataFrame(rows)

    return df_rows, first_month


# ============================================================
# Weather variable groups for selection
# ============================================================
GROUPS = {
    "temp": {
        "label": "Temperature (°C)",
        "cols": ["temperature_2m (°C)"],
    },
    "wind": {
        "label": "Wind (m/s)",
        "cols": ["wind_speed_10m (m/s)", "wind_gusts_10m (m/s)"],
    },
    "precip": {
        "label": "Precipitation (mm)",
        "cols": ["precipitation (mm)"],
    },
    "wdir": {
        "label": "Wind direction (°)",
        "cols": ["wind_direction_10m (°)"],
    },
}


# ============================================================
# Robust variable name normalizer
# ============================================================
def normalize_varname(name: str) -> str:
    """Normalize variable names for consistent matching."""
    return (
        name.lower()
        .replace(" ", "")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "")
        .replace("_10m", "")
        .replace("2m", "")
        .replace("m/s", "")
    )


# ============================================================
# Color mapping — consistent across both modes
# ============================================================
COLOR_MAP = {
    "temperature": "#DF0000",
    "windspeed": "#F93A8D",
    "windgusts": "#7D3CFF",
    "precipitation": "#004BA1",
    "winddirection": "#404040",
}


def get_color(varname: str):
    norm = normalize_varname(varname)
    for key, col in COLOR_MAP.items():
        if key in norm:
            return col
    return "#222222"  # fallback dark gray


# ============================================================
# Main plotting function
# ============================================================
def plot_weather(df, cols, month_label, mode="Auto-axes", method=None):
    """
    Interactive weather plot with clean axis management.
    Colors must be consistent in both auto-scale and normalized modes.
    """
    if df.empty or not cols:
        fig = go.Figure()
        fig.update_layout(title="No data selected", template="plotly_white")
        return fig

    fig = go.Figure()

    # ------------------------------------------------------------
    # Normalize if requested
    # ------------------------------------------------------------
    if mode.startswith("Normalize") and method:
        df_norm = df.copy()
        for c in cols:
            x = df[c].astype(float)
            if method == "Z-score":
                df_norm[c] = (x - np.nanmean(x)) / np.nanstd(x)
            elif method.startswith("Min"):
                df_norm[c] = (x - np.nanmin(x)) / (np.nanmax(x) - np.nanmin(x))
            elif method.startswith("Index"):
                df_norm[c] = (x / x.iloc[0]) * 100 if x.iloc[0] != 0 else x
        df_plot = df_norm
    else:
        df_plot = df

    # ------------------------------------------------------------
    # Assign roles to variables
    # ------------------------------------------------------------
    precip_vars = [c for c in cols if "precip" in c.lower()]
    dir_vars = [c for c in cols if "direction" in c.lower()]
    main_vars = [c for c in cols if c not in precip_vars + dir_vars]

    # ------------------------------------------------------------
    # AUTO-AXES MODE
    # ------------------------------------------------------------
    if not mode.startswith("Normalize"):

        # Main line variables
        for c in main_vars:
            fig.add_trace(
                go.Scatter(
                    x=df_plot["time"],
                    y=df_plot[c],
                    mode="lines",
                    name=c,
                    line=dict(
                        width=1.5,
                        color=get_color(c),
                    ),
                    yaxis="y1",
                )
            )

        # Precipitation
        for c in precip_vars:
            fig.add_trace(
                go.Bar(
                    x=df_plot["time"],
                    y=df_plot[c],
                    name=c,
                    marker_color=get_color(c),
                    opacity=0.45,
                    yaxis="y2",
                )
            )

        # Wind direction
        for c in dir_vars:
            fig.add_trace(
                go.Scatter(
                    x=df_plot["time"],
                    y=df_plot[c],
                    name=c,
                    mode="lines",
                    line=dict(
                        width=1,
                        dash="dot",
                        color=get_color(c),
                    ),
                    yaxis="y3",
                )
            )

        fig.update_layout(
            yaxis=dict(title="Temperature / Wind", showgrid=True),
            yaxis2=dict(
                title="Precipitation (mm)",
                overlaying="y",
                side="right",
                showgrid=False,
                position=0.94,
            ),
            yaxis3=dict(
                title="Wind Direction (°)",
                overlaying="y",
                side="right",
                showgrid=False,
                position=1.00,
            ),
        )

    # ------------------------------------------------------------
    # NORMALIZED MODE
    # ------------------------------------------------------------
    else:
        for c in cols:
            fig.add_trace(
                go.Scatter(
                    x=df_plot["time"],
                    y=df_plot[c],
                    mode="lines",
                    name=c,
                    line=dict(
                        width=1.5,
                        color=get_color(c),  # <-- Consistent colors here
                    ),
                )
            )

        fig.update_layout(yaxis=dict(title="Normalized scale"))

    # ------------------------------------------------------------
    # COMMON LAYOUT
    # ------------------------------------------------------------
    fig.update_layout(
        title=f"Weather Variables — {month_label}",
        template="plotly_white",
        xaxis_title="Time",
        legend=dict(orientation="h", y=-0.25),
        height=600,
        margin=dict(l=60, r=80, t=80, b=50),
        barmode="overlay",
    )

    return fig


# STL decomposition plot function
def plot_stl_decomposition(df, seasonal=30, trend=90):
    """
    Plot STL decomposition (trend, seasonal, residual) for production data.

    Parameters
    ----------
    df : DataFrame
        Must contain columns ["starttime", "quantitykwh"].
    seasonal : int
        Length of seasonal smoothing window.
    trend : int
        Length of trend smoothing window.

    Returns
    -------
    fig : plotly.graph_objects.Figure
        Interactive decomposition chart.
    """
    # --- Prepare time series (aggregate duplicates to 1-hour frequency) ---
    ts = (
        df.groupby("starttime", as_index=True)["quantitykwh"]
        .sum()
        .asfreq("h")
        .interpolate()
    )

    # --- Perform STL decomposition ---
    stl = STL(ts, seasonal=seasonal, trend=trend, robust=True)
    res = stl.fit()

    # --- Create subplots (stacked vertically) ---
    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        subplot_titles=("Original Series", "Trend", "Seasonal", "Residuals"),
        vertical_spacing=0.08,
    )

    # Original
    fig.add_trace(
        go.Scatter(
            x=ts.index, y=ts.values, name="Original", line=dict(color="#4c78a8")
        ),
        row=1,
        col=1,
    )

    # Trend
    fig.add_trace(
        go.Scatter(x=ts.index, y=res.trend, name="Trend", line=dict(color="#f58518")),
        row=2,
        col=1,
    )

    # Seasonal
    fig.add_trace(
        go.Scatter(
            x=ts.index, y=res.seasonal, name="Seasonal", line=dict(color="#54a24b")
        ),
        row=3,
        col=1,
    )

    # Residual
    fig.add_trace(
        go.Scatter(
            x=ts.index, y=res.resid, name="Residuals", line=dict(color="#e45756")
        ),
        row=4,
        col=1,
    )

    # --- Layout ---
    fig.update_layout(
        height=800,
        title=f"STL Decomposition – Seasonal={seasonal}, Trend={trend}",
        showlegend=False,
        template="plotly_dark",
        margin=dict(t=80, b=40),
    )
    fig.update_xaxes(title="Time", row=4, col=1)
    fig.update_yaxes(title="kWh")

    return fig


# Spectrogram plot function
def plot_spectrogram(df, window=168, overlap=50):
    """
    Plot a frequency spectrogram for production data.

    Parameters
    ----------
    df : DataFrame
        Must contain columns ["starttime", "quantitykwh"].
    window : int
        Window length in hours.
    overlap : int
        Percentage of overlap between windows (0–90).

    Returns
    -------
    fig : plotly.graph_objects.Figure
        Spectrogram heatmap.
    """
    if len(df) < window:
        raise ValueError("Data length is shorter than the window size.")

    # --- Prepare series ---
    # --- Prepare time series (aggregate duplicates to 1-hour frequency) ---
    ts = (
        df.groupby("starttime", as_index=True)["quantitykwh"]
        .sum()
        .asfreq("h")
        .interpolate()
    )
    nperseg = window
    noverlap = int(window * (overlap / 100))

    # --- Compute spectrogram ---
    f, t, Sxx = spectrogram(ts.values, fs=1.0, nperseg=nperseg, noverlap=noverlap)
    Sxx_db = 10 * np.log10(Sxx + 1e-10)

    # --- Time axis mapping ---
    time_labels = pd.to_datetime(ts.index[0]) + pd.to_timedelta(t, unit="h")

    # --- Plotly heatmap ---
    fig = go.Figure(
        data=go.Heatmap(
            z=Sxx_db,
            x=time_labels,
            y=f,
            colorscale="Viridis",
            colorbar=dict(title="Power (dB)"),
        )
    )

    fig.update_layout(
        title=f"Spectrogram – Window={window}h, Overlap={overlap}%",
        xaxis_title="Time",
        yaxis_title="Frequency [cycles/hour]",
        height=600,
        template="plotly_dark",
        margin=dict(t=70, b=40),
    )

    return fig
