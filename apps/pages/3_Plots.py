from pathlib import Path
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

st.title("📈 Plots")


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(Path().cwd() / "data" / "open-meteo-subset.csv")
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    return df.dropna(subset=["time"])


df = load_data()

# choose columns
all_cols = [c for c in df.columns if c != "time"]
select_all = st.checkbox("Select all columns", value=False)
selected = st.multiselect(
    "Select columns (multiple allowed)",
    options=all_cols,
    default=(all_cols if select_all else []),
)
cols = selected or all_cols

# subset per month
df["month"] = df["time"].dt.to_period("M").astype(str)
months = sorted(df["month"].unique())
month_sel = st.select_slider("Select month", options=months, value=months[0])
data = df[df["month"] == month_sel].reset_index(drop=True)

# groups (used for auto-axes)
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
groups_in_use = [
    g for g, meta in GROUPS.items() if any(c in cols for c in meta["cols"])
]

mode = st.radio("View", ["Auto-axes", "Normalize (common scale)"], horizontal=True)


# helpers
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


# plot
fig, axA = plt.subplots(figsize=(14, 5))

if mode.startswith("Normalize"):
    method = st.selectbox("Method", ["Z-score", "Min–max (0–1)", "Index 100 at start"])
    dfn, ylab = normalize_frame(data, cols, method)
    for c in cols:
        axA.plot(dfn["time"], dfn[c], lw=1.2, label=c)
    axA.set_ylabel(ylab)
    axA.legend(ncol=2, fontsize=9, loc="upper left")

else:
    # Up to 4 axes: A (left), B (right), C (right 1.10), D (right 1.20)
    axes = {"A": axA}
    order = ["temp", "wind", "precip", "wdir"]  # deterministic order
    used = [g for g in order if g in groups_in_use]

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

    # Map group → axis
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
st.pyplot(fig)

st.caption(
    "Select *Normalize* manually when you want to compare shapes on a single scale. "
    "In *Auto-axes*, temperature, wind, precipitation and wind direction get their own axes (up to four)."
)
