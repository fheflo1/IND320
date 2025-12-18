import numpy as np
import pandas as pd
from scipy.fftpack import dct, idct
from sklearn.neighbors import LocalOutlierFactor


def detect_temperature_outliers(df, cutoff=0.1, std_thresh=2.0):
    """
    Detect temperature outliers using SATV (DCT high-pass) + SPC.

    Steps:
    1. Smooth temperature with low-pass DCT to remove noise.
    2. Compute SATV = temperature - smoothed.
    3. Compute SPC limits from SATV only.
    4. Outliers = original temperature where SATV is outside SPC limits.
    5. Provide temperature-domain boundaries (smoothed + LCL/UCL) that
       define the non-outlier interval for plotting.

    Returns:
        DataFrame with columns:
        [time, temperature, smoothed, SATV, UCL, LCL, upper_bound, lower_bound, outlier, inlier]
    """

    df = df.copy().dropna(subset=["temperature_2m"])
    df = df.sort_values("time")

    temps = df["temperature_2m"].to_numpy()
    n = len(temps)

    if n < 20:
        raise ValueError("Not enough data points for SATV/SPC.")

    # 1. DCT smoothing (low-pass)
    coeffs = dct(temps, norm="ortho")
    k = int(cutoff * n)
    lp = coeffs.copy()
    lp[k:] = 0  # low-pass filter
    smoothed = idct(lp, norm="ortho")

    # 2. Compute SATV (high-pass)
    satv = temps - smoothed

    # 3. SPC bounds computed on SATV ONLY
    mu = np.mean(satv)
    sigma = np.std(satv)
    UCL = mu + std_thresh * sigma
    LCL = mu - std_thresh * sigma

    # 4. Outlier locations (SATV exceeds limits)
    outliers = (satv > UCL) | (satv < LCL)
    inliers = ~outliers

    # 5. Temperature-domain boundaries for non-outlier interval:
    #    everything between these is NOT an outlier.
    lower_bound = smoothed + LCL
    upper_bound = smoothed + UCL

    return pd.DataFrame(
        {
            "time": df["time"].to_numpy(),
            "temperature": temps,
            "smoothed": smoothed,
            "SATV": satv,
            "UCL": np.full(n, UCL),
            "LCL": np.full(n, LCL),
            "upper_bound": upper_bound,
            "lower_bound": lower_bound,
            "outlier": outliers,
            "inlier": inliers,
        }
    )


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

    df_out = pd.DataFrame(
        {
            "time": df["time"],
            "precipitation": df["precipitation"],
            "anomaly": anomaly,
        }
    )
    return df_out
