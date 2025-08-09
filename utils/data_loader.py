# utils/data_loader.py
import pandas as pd

REQUIRED = {"date", "PRICE", "IV", "HV10", "HV20", "HV30", "Spread", "Spread_z"}


def load_market_data(path="data/blatality_dataset.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {path}: {sorted(missing)}")

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").dropna(subset=["PRICE", "IV"])

    # Normalize names for the rest of your codebase
    df = df.rename(
        columns={
            "PRICE": "spot",
            "IV": "iv",
            "HV10": "hv10",
            "HV20": "hv20",
            "HV30": "hv30",
            "Spread": "spread",
            "Spread_z": "z",
        }
    )
    return df[["date", "spot", "iv", "hv10", "hv20", "hv30", "spread", "z"]]
