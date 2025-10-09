import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize, TwoSlopeNorm
import numpy as np
import pandas as pd

plt.style.use("dark_background")
plt.rcParams.update(
    {
        "figure.facecolor": "black",
        "axes.facecolor": "black",
        "savefig.facecolor": "black",
        "axes.edgecolor": "white",
        "axes.labelcolor": "white",
        "xtick.color": "white",
        "ytick.color": "white",
        "axes.titlecolor": "white",
        "text.color": "white",
        "grid.color": "gray",
    }
)


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
        "style": dict(lw=1.5, color=None),
    },
    "wind": {
        "label": "Wind (m/s)",
        "cols": ["wind_speed_10m (m/s)", "wind_gusts_10m (m/s)"],
        "style": dict(lw=1.2, color=None),
    },
    "precip": {
        "label": "Precipitation (mm)",
        "cols": ["precipitation (mm)"],
        "style": dict(alpha=0.25),
    },
    "wdir": {
        "label": "Wind direction (°)",
        "cols": ["wind_direction_10m (°)"],
        "style": dict(lw=1.0, linestyle=":"),
    },
}


def set_monthly_ticks(ax):
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.tick_params(axis="x", rotation=45)


def set_cardinal_ticks(ax):
    ticks = [0, 45, 90, 135, 180, 225, 270, 315, 360]
    labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"]
    ax.set_yticks(ticks)
    ax.set_yticklabels(labels)
    ax.set_ylim(0, 360)


def normalize_frame(frame: pd.DataFrame, cols: list[str], method: str):
    g = frame.copy()
    if method == "Z-score":
        for c in cols:
            g[c] = (g[c] - g[c].mean()) / g[c].std(ddof=0)
        return g, "Standardized value (z-score)"
    if method == "Min–max (0–1)":
        for c in cols:
            rng = (g[c].max() - g[c].min()) or 1.0
            g[c] = (g[c] - g[c].min()) / rng
        return g, "Scaled 0–1"
    if method == "Index 100 at start":
        for c in cols:
            base = g[c].iloc[0] or 1.0
            g[c] = g[c] / base * 100.0
        return g, "Index (start=100)"
    return g, "Value"


def plot_weather(
    data: pd.DataFrame,
    cols: list[str],
    month_sel: str,
    mode: str,
    method: str | None = None,
):
    """
    Lager figur for valgt måned og kolonner.
    mode: "Normalize" eller "Auto-axes"
    """
    fig, axA = plt.subplots(figsize=(14, 5))

    if mode.startswith("Normalize"):
        dfn, ylab = normalize_frame(data, cols, method)
        for c in cols:
            axA.plot(dfn["time"], dfn[c], lw=1.2, label=c)
        axA.set_ylabel(ylab)
        axA.legend(ncol=2, fontsize=9, loc="upper left")

    else:
        axes = {"A": axA}
        order = ["temp", "wind", "precip", "wdir"]
        used = [g for g in order if any(c in cols for c in GROUPS[g]["cols"])]

        if len(used) >= 2:
            axes["B"] = axA.twinx()
        if len(used) >= 3:
            axC = axA.twinx()
            axC.spines["right"].set_position(("axes", 1.10))
            axC.set_frame_on(True)
            axC.patch.set_visible(False)
            axes["C"] = axC
        if len(used) >= 4:
            axD = axA.twinx()
            axD.spines["right"].set_position(("axes", 1.20))
            axD.set_frame_on(True)
            axD.patch.set_visible(False)
            axes["D"] = axD

        axis_keys = list(axes.keys())
        group_axis = {g: axis_keys[i] for i, g in enumerate(used)}

        handles, labels = [], []
        for g in used:
            ax = axes[group_axis[g]]
            meta = GROUPS[g]
            gcols = [c for c in meta["cols"] if c in cols]
            if g == "precip":
                y = data[gcols[0]].rolling(24, min_periods=1).sum()
                h = ax.fill_between(
                    data["time"], 0, y, label="Precip 24h sum (mm)", **meta["style"]
                )
            else:
                for c in gcols:
                    h = ax.plot(data["time"], data[c], label=c, **meta["style"])[0]
            ax.set_ylabel(meta["label"])
            if g == "wdir":
                set_cardinal_ticks(ax)
            h_, l_ = ax.get_legend_handles_labels()
            handles += h_
            labels += l_

        axA.legend(handles, labels, ncol=2, fontsize=9, loc="upper left")

    axA.set_title(f"Weather – {month_sel}")
    axA.set_xlabel("Time")
    set_monthly_ticks(axA)
    axA.grid(alpha=0.3)
    fig.tight_layout()
    return fig
