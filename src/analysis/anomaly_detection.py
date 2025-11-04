import numpy as np
import pandas as pd
from scipy.fftpack import dct, idct
from sklearn.neighbors import LocalOutlierFactor


# ------------------------------------------------------------
# 1️⃣ Temperature Outlier Detection (SPC + DCT smoothing)
# ------------------------------------------------------------
def detect_temperature_outliers(df, cutoff=0.05, std_thresh=3.0):
    """
    Detect temperature outliers using DCT low-pass filtering + SPC bounds.

    Parameters
    ----------
    df : DataFrame
        Must contain ["time", "temperature_2m"].
    cutoff : float
        Frequency cutoff for DCT (fraction of coefficients kept).
    std_thresh : float
        STD-based threshold for control limits.

    Returns
    -------
    df_out : DataFrame with columns [time, temp, smoothed, outlier, UCL, LCL].
    """
    df = df.copy()
    df = df.dropna(subset=["temperature_2m"])
    df = df.sort_values("time")

    temps = df["temperature_2m"].to_numpy()
    n = len(temps)
    if n < 10:
        raise ValueError("Not enough temperature data.")

    # --- DCT low-pass smoothing ---
    coeffs = dct(temps, norm="ortho")
    k = int(cutoff * n)
    coeffs[k:] = 0
    smoothed = idct(coeffs, norm="ortho")

    # --- SPC limits ---
    mu = np.mean(smoothed)
    sigma = np.std(smoothed)
    UCL, LCL = mu + std_thresh * sigma, mu - std_thresh * sigma
    outliers = (temps > UCL) | (temps < LCL)

    df_out = pd.DataFrame({
        "time": df["time"],
        "temperature": temps,
        "smoothed": smoothed,
        "UCL": UCL,
        "LCL": LCL,
        "outlier": outliers,
    })
    return df_out


# ------------------------------------------------------------
# 2️⃣ Precipitation Anomaly Detection (LOF)
# ------------------------------------------------------------
def detect_precipitation_anomalies(df, outlier_prop=0.01):
    """
    Detect precipitation anomalies using Local Outlier Factor (LOF).

    Parameters
    ----------
    df : DataFrame
        Must contain ["time", "precipitation"].
    outlier_prop : float
        Proportion of expected anomalies (0.01 = 1 %).

    Returns
    -------
    df_out : DataFrame with columns [time, precipitation, anomaly].
    """
    df = df.copy()
    df = df.dropna(subset=["precipitation"])
    df = df.sort_values("time")

    vals = df["precipitation"].to_numpy().reshape(-1, 1)
    n_neighbors = max(10, int(len(vals) * outlier_prop * 5))

    lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=outlier_prop)
    preds = lof.fit_predict(vals)
    anomaly = preds == -1

    df_out = pd.DataFrame({
        "time": df["time"],
        "precipitation": df["precipitation"],
        "anomaly": anomaly,
    })
    return df_out
