import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

# Setup the Open-Meteo API client with cache and retries
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

BASE_URL = "https://archive-api.open-meteo.com/v1/era5"

def fetch_meteo_data(lat: float, lon: float,
                     start_date: str, end_date: str,
                     variables: list[str] = None) -> pd.DataFrame:
    """
    Fetch ERA5 historical data for a given location and time range.
    Uses official Open-Meteo SDK with caching and retry logic.
    """
    if variables is None:
        variables = ["temperature_2m", "precipitation"]

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join(variables),
        "timezone": "Europe/Oslo"
    }

    responses = openmeteo.weather_api(BASE_URL, params=params)
    response = responses[0]  # single location query

    hourly = response.Hourly()
    data = {"time": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        periods=hourly.Variables(0).ValuesAsNumpy().size,
        freq=pd.Timedelta(seconds=hourly.Interval())
    )}

    for i, var in enumerate(variables):
        data[var] = hourly.Variables(i).ValuesAsNumpy()

    df = pd.DataFrame(data)
    df["time"] = pd.to_datetime(df["time"]).dt.tz_convert("Europe/Oslo")
    df = df.set_index("time")

    return df
