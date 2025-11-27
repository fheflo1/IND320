import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
import streamlit as st


@st.cache_data(show_spinner=False)
def prepare_data(df, target_col, start_date, end_date, exog_cols=None):
    """
    Slice and return target + exogenous. Cache because this step is pure.
    """
    df = df.copy()
    dff = df.loc[start_date:end_date]

    y = dff[target_col]

    if exog_cols:
        X = dff[exog_cols]
    else:
        X = None

    return y, X


def fit_sarimax(y, X, order, seasonal_order):
    """
    Model fitting cannot be cached safely because SARIMAX objects are not pickle-safe.
    """
    model = SARIMAX(
        y,
        exog=X,
        order=order,
        seasonal_order=seasonal_order,
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    return model.fit(disp=False)


def run_forecast(model_params, steps, X_future):
    """
    Cache forecast results based on model parameters, steps and exog future.
    NOTE: We cache *results*, not the model object.
    """
    model, order, seasonal_order, y, X = model_params

    pred = model.get_forecast(steps=steps, exog=X_future)
    forecast_mean = pred.predicted_mean
    conf_int = pred.conf_int()
    lower = conf_int.iloc[:, 0]
    upper = conf_int.iloc[:, 1]

    return forecast_mean, lower, upper
