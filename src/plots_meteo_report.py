import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.fftpack import dct, idct

# ======================================================
# 1️⃣ Temperature Outlier Plot (SPC)
# ======================================================
def plot_temperature_outliers(df, freq_cutoff, std_thresh):
    """
    Plot temperature signal with DCT filtering and SPC-based outlier highlighting.
    
    Parameters
    ----------
    df : pd.DataFrame
        Must contain columns ['time', 'temperature_2m'].
    freq_cutoff : int
        Frequency cutoff for DCT filtering (low frequencies kept).
    std_thresh : float
        Standard deviation threshold for outlier detection.
    """
    df = df.copy()
    df["time"] = pd.to_datetime(df["time"])
    df = df.set_index("time").sort_index()

    # --- DCT filtering ---
    y = df["temperature_2m"].values
    y_dct = dct(y, norm="ortho")
    y_dct[freq_cutoff:] = 0
    y_smooth = idct(y_dct, norm="ortho")

    df["filtered"] = y_smooth
    df["residual"] = df["temperature_2m"] - df["filtered"]

    # --- Outlier detection ---
    std = df["residual"].std()
    df["outlier"] = np.abs(df["residual"]) > std_thresh * std

    # --- Plot ---
    plt.figure(figsize=(12, 5))
    plt.plot(df.index, df["temperature_2m"], color="gray", alpha=0.6, label="Observed")
    plt.plot(df.index, df["filtered"], color="blue", linewidth=1.5, label="Filtered signal")
    plt.scatter(
        df.index[df["outlier"]],
        df.loc[df["outlier"], "temperature_2m"],
        color="red", s=25, label="Outliers"
    )
    plt.title(f"Temperature Outlier Detection (cutoff={freq_cutoff}, ±{std_thresh}σ)")
    plt.xlabel("Time")
    plt.ylabel("Temperature (°C)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()


# ======================================================
# 2️⃣ Precipitation Anomaly Plot (LOF)
# ======================================================
from sklearn.neighbors import LocalOutlierFactor

def plot_precipitation_anomalies(df, contamination=0.01):
    """
    Plot precipitation data with anomalies detected using LOF.
    
    Parameters
    ----------
    df : pd.DataFrame
        Must contain columns ['time', 'precipitation'].
    contamination : float
        Proportion of points to mark as anomalies.
    """
    df = df.copy()
    df["time"] = pd.to_datetime(df["time"])
    df = df.set_index("time").sort_index()

    # --- LOF detection ---
    lof = LocalOutlierFactor(contamination=contamination)
    preds = lof.fit_predict(df[["precipitation"]])
    df["anomaly"] = preds == -1

    # --- Plot ---
    plt.figure(figsize=(12, 5))
    plt.plot(df.index, df["precipitation"], color="blue", linewidth=1, label="Precipitation")
    plt.scatter(
        df.index[df["anomaly"]],
        df.loc[df["anomaly"], "precipitation"],
        color="red", s=25, label="Anomalies"
    )
    plt.title(f"Precipitation Anomaly Detection (LOF, {int(contamination*100)}%)")
    plt.xlabel("Time")
    plt.ylabel("Precipitation (mm)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()
