import numpy as np
import pandas as pd
import plotly.graph_objects as go


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


# Plots for page 3_Plots.py
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



def plot_weather(df, cols, month_label, mode="Auto-axes", method=None):
    """
    Interactive weather plot with clean axis management.
    """
    if df.empty or not cols:
        fig = go.Figure()
        fig.update_layout(title="No data selected", template="plotly_white")
        return fig

    fig = go.Figure()

    # Normalize if requested
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

    # Assign roles to variables
    precip_vars = [c for c in cols if "precip" in c.lower()]
    dir_vars = [c for c in cols if "direction" in c.lower()]
    main_vars = [c for c in cols if c not in precip_vars + dir_vars]

    # --- Auto-axes mode ---
    if not mode.startswith("Normalize"):
        for c in main_vars:
            fig.add_trace(
                go.Scatter(
                    x=df_plot["time"],
                    y=df_plot[c],
                    mode="lines",
                    name=c,
                    line=dict(width=1.5),
                    yaxis="y1",
                )
            )

        for c in precip_vars:
            fig.add_trace(
                go.Bar(
                    x=df_plot["time"],
                    y=df_plot[c],
                    name=c,
                    marker_color="deepskyblue",
                    opacity=0.4,
                    yaxis="y2",
                )
            )

        for c in dir_vars:
            fig.add_trace(
                go.Scatter(
                    x=df_plot["time"],
                    y=df_plot[c],
                    name=c,
                    mode="lines",
                    line=dict(width=1, dash="dot", color="orange"),
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
                position=0.94,   # just inside plot area
            ),
            yaxis3=dict(
                title="Wind Direction (°)",
                overlaying="y",
                side="right",
                showgrid=False,
                position=1.0,    # aligned at far right edge
            ),
        )

    # --- Normalized mode ---
    else:
        for c in cols:
            fig.add_trace(
                go.Scatter(
                    x=df_plot["time"],
                    y=df_plot[c],
                    mode="lines",
                    name=c,
                    line=dict(width=1.5),
                )
            )
        fig.update_layout(yaxis=dict(title="Normalized scale"))

    # --- Common layout ---
    fig.update_layout(
        title=f"Weather Variables — {month_label}",
        template="plotly_white",
        xaxis_title="Time",
        legend=dict(orientation="h", y=-0.3),
        height=600,
        margin=dict(l=60, r=80, t=80, b=50),
        barmode="overlay",
    )

    return fig
