import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize, TwoSlopeNorm
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# plt.style.use("dark_background")
# plt.rcParams.update(
#     {
#         "figure.facecolor": "black",
#         "axes.facecolor": "black",
#         "savefig.facecolor": "black",
#         "axes.edgecolor": "white",
#         "axes.labelcolor": "white",
#         "xtick.color": "white",
#         "ytick.color": "white",
#         "axes.titlecolor": "white",
#         "text.color": "white",
#         "grid.color": "gray",
#     }
# )


def plot_diverging_line(df, col: str):
    """Plot a line with color interpolation. Handles diverging (center=0) or only positive/negative values."""
    # use dark background and force fully black faces and white text/ticks

    y = df[col].values
    x = pd.to_datetime(df["time"])
    x_nums = mdates.date2num(x)

    # Bygg segmenter
    points = np.array([x_nums, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    # Velg colormap og normalisering
    if y.min() < 0 and y.max() > 0:
        norm = TwoSlopeNorm(vmin=y.min(), vcenter=0.0, vmax=y.max())
        cmap = "coolwarm"
    else:
        norm = Normalize(vmin=y.min(), vmax=y.max())
        cmap = "Spectral"

    lc = LineCollection(segments, cmap=cmap, norm=norm, linewidth=2)
    lc.set_array((y[:-1] + y[1:]) / 2)

    # Plot
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.add_collection(lc)
    ax.set_xlim(x_nums.min(), x_nums.max())
    ax.set_ylim(y.min() - 1, y.max() + 1)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

    ax.set_title(f"{col} over tid")
    ax.set_xlabel("Time")
    ax.set_ylabel(col)
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.colorbar(lc, ax=ax, label=col)
    plt.tight_layout()

    return fig


def prepare_first_month_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tar et DataFrame med en 'time'-kolonne og returnerer et DataFrame
    med én rad per numerisk kolonne og en LineChartColumn-kompatibel liste
    med verdier for den første måneden i datasettet.
    """

    # Konverter tid
    df = df.copy()
    df["time"] = pd.to_datetime(df["time"])

    # Finn første måned
    first_month = df["time"].dt.to_period("M").min()
    fm = df[df["time"].dt.to_period("M") == first_month].reset_index(drop=True)

    # Kun numeriske kolonner
    num_cols = fm.select_dtypes(include="number").columns.tolist()

    # Bygg "table" format
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


def plot_weather(data, cols, month_sel, mode, method=None):
    fig = go.Figure()

    order = ["temp", "wind", "precip", "wdir"]
    used = [g for g in order if any(c in cols for c in GROUPS[g]["cols"])]

    # Determine normalization method. Support several user strings and fall back to None
    raw_choice = (method or mode or "").strip().lower()
    if raw_choice in ("", "raw", "none", "no"):
        norm_method = None
    elif raw_choice in ("normalized", "norm", "minmax", "min-max", "max-min"):
        norm_method = "minmax"
    elif raw_choice in ("zscore", "z-score", "std", "standardize"):
        norm_method = "zscore"
    elif raw_choice in ("index", "indexed", "relative"):
        norm_method = "index"
    else:
        # unknown option -> treat as raw
        norm_method = None

    normalized_mode = norm_method is not None

    # If only one column selected or in normalized mode, use the full horizontal space
    full_width = len(cols) == 1 or normalized_mode

    # Define x-domain: use full width when requested, otherwise leave room for right-side axes
    fig.update_layout(xaxis=dict(domain=[0, 1.0] if full_width else [0, 0.82]))

    # --- Add traces and axis setup ---
    # If not full_width, distribute right-side axes in the reserved space; otherwise no right-side axes
    axis_positions = (
        np.linspace(0.83, 0.98, max(1, len(used))) if not full_width else np.array([0.98])
    )

    if normalized_mode:
        # Single normalized left axis: apply chosen normalization to every series and plot on the left
        for g in used:
            meta = GROUPS[g]
            gcols = [c for c in meta["cols"] if c in cols]
            for c in gcols:
                if g == "precip":
                    series = data[c].rolling(24, min_periods=1).sum().astype(float)
                    name_base = "Precip 24h sum"
                else:
                    series = data[c].astype(float)
                    name_base = c

                arr = series.values.astype(float)
                valid = ~np.isnan(arr)

                if not valid.any():
                    arr_norm = np.full_like(arr, np.nan, dtype=float)
                else:
                    if norm_method == "minmax":
                        vmin = np.nanmin(arr)
                        vmax = np.nanmax(arr)
                        if np.isclose(vmax, vmin):
                            arr_norm = np.where(valid, 0.0, np.nan)
                        else:
                            arr_norm = (arr - vmin) / (vmax - vmin)
                    elif norm_method == "zscore":
                        mean = np.nanmean(arr)
                        std = np.nanstd(arr)
                        if np.isclose(std, 0.0):
                            arr_norm = np.where(valid, 0.0, np.nan)
                        else:
                            arr_norm = (arr - mean) / std
                    elif norm_method == "index":
                        # index to first valid value, scale so first valid = 100
                        first_idx = np.where(valid)[0][0]
                        base = arr[first_idx]
                        if np.isclose(base, 0.0):
                            arr_norm = np.where(valid, np.nan, np.nan)
                        else:
                            arr_norm = (arr / base) * 100.0
                    else:
                        arr_norm = arr  # fallback: raw

                display_name = f"{name_base} ({norm_method})" if norm_method else name_base

                fig.add_trace(go.Scatter(
                    x=data["time"],
                    y=arr_norm,
                    mode="lines",
                    name=display_name,
                    yaxis="y"  # left normalized axis
                ))

        # Configure only the left normalized axis
        yaxis_cfg = dict(
            title=f"{'Normalized (0-1)' if norm_method=='minmax' else ('Z-score' if norm_method=='zscore' else 'Indexed (first=100)')}",
            showgrid=False,
            side="left",
        )
        if norm_method == "minmax":
            yaxis_cfg["range"] = [0, 1]

        fig.layout["yaxis"] = yaxis_cfg

    else:
        # Non-normalized mode: keep at least one axis on left, additional axes on right
        for i, (g, pos) in enumerate(zip(used, axis_positions)):
            # axis identifiers used in traces: 'y' for first, 'y2'/'y3'... for others
            axis_id_trace = "y" if i == 0 else f"y{i+1}"
            axis_name = "yaxis" if i == 0 else f"yaxis{i+1}"
            meta = GROUPS[g]
            gcols = [c for c in meta["cols"] if c in cols]

            # Add traces for group
            if g == "precip":
                y = data[gcols[0]].rolling(24, min_periods=1).sum()
                fig.add_trace(go.Scatter(
                    x=data["time"],
                    y=y,
                    name="Precip 24h sum (mm)",
                    fill="tozeroy",
                    opacity=0.4,
                    yaxis=axis_id_trace
                ))
            else:
                for c in gcols:
                    fig.add_trace(go.Scatter(
                        x=data["time"],
                        y=data[c],
                        mode="lines",
                        name=c,
                        yaxis=axis_id_trace
                    ))

            # Axis config: first axis stays on the left (no position set), others on the right and overlay the left
            axis_settings = dict(
                title=meta["label"],
                showgrid=False,
                side="left" if i == 0 else "right",
            )
            if i > 0:
                axis_settings["overlaying"] = "y"
                axis_settings["position"] = float(pos)

            # Special ticks for wind direction
            if g == "wdir":
                ticks = np.linspace(0, 360, 9)
                labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"]
                axis_settings.update(
                    tickmode="array",
                    tickvals=ticks,
                    ticktext=labels,
                    range=[0, 360]
                )

            fig.layout[axis_name] = axis_settings

    # --- Layout styling ---
    fig.update_layout(
        title=f"Weather – {month_sel}",
        xaxis_title="Time",
        template="plotly_dark",
        margin=dict(l=40, r=140, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
    )

    return fig
