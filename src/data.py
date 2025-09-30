from pathlib import Path
import pandas as pd

def project_root() -> Path:
    """Returnerer prosjektroten (mappa som inneholder src/ og data/)."""
    return Path(__file__).resolve().parents[1]

def load_csv() -> pd.DataFrame:
    """Laster inn open-meteo-subset.csv fra data/-mappa."""
    root = project_root()
    csv_path = root / "data" / "open-meteo-subset.csv"

    if not csv_path.exists():
        raise FileNotFoundError(f"Fant ikke CSV-filen: {csv_path}")

    df = pd.read_csv(csv_path)
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    return df.dropna(subset=["time"])

