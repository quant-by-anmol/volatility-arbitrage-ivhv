# scripts/update_data.py
import argparse
import os
import time

import numpy as np
import pandas as pd
import yfinance as yf


def _fetch_one(
    ticker: str, start: str, end: str | None, tries: int = 6
) -> pd.DataFrame:
    """Robust daily close fetcher. Returns ['date','close'] with numeric close."""
    for i in range(1, tries + 1):
        try:
            df = yf.Ticker(ticker).history(
                start=start, end=end, interval="1d", auto_adjust=False, actions=False
            )
            if df is None or df.empty:
                raise ValueError("Empty dataframe")

            df = df.rename_axis("date").reset_index()
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df["date"] = df["date"].dt.tz_localize(None).dt.normalize()

            # find Close column (works across yfinance variants)
            close_col = None
            if isinstance(df.columns, pd.MultiIndex):
                for col in df.columns:
                    if (
                        isinstance(col, tuple)
                        and str(col[0]).strip().lower() == "close"
                    ):
                        close_col = col
                        break
            if close_col is None:
                for c in df.columns:
                    if "close" in str(c).lower():
                        close_col = c
                        break
            if close_col is None:
                raise KeyError(f"No Close col in {list(df.columns)}")

            out = df[["date", close_col]].rename(columns={close_col: "close"})
            out["close"] = pd.to_numeric(out["close"], errors="coerce")
            out = out.dropna()
            if out.empty:
                raise ValueError("All-close NaN after coercion")
            return out
        except Exception as e:
            wait = min(60, 2**i)
            print(f"[{ticker}] try {i} failed: {e}. Sleeping {wait}s...")
            time.sleep(wait)
    raise RuntimeError(f"Failed to fetch {ticker} after retries.")


def realized_vol(close: pd.Series, window: int, trading_days: int = 252) -> pd.Series:
    rets = np.log(close).diff()
    return rets.rolling(window).std(ddof=0) * np.sqrt(trading_days) * 100.0


def zscore(s: pd.Series, window: int) -> pd.Series:
    m = s.rolling(window).mean()
    sd = s.rolling(window).std(ddof=0)
    return (s - m) / sd


def atomic_write_csv(df: pd.DataFrame, path: str):
    tmp = path + ".tmp"
    df.to_csv(tmp, index=False)
    os.replace(tmp, path)


def main(
    price: str,
    iv: str,
    start: str,
    end: str | None,
    hv_windows=(10, 20, 30),
    z_window=60,
    out_path="data/blatality_dataset.csv",
):
    px = _fetch_one(price, start, end).rename(columns={"close": "PRICE"})
    ivd = _fetch_one(iv, start, end).rename(columns={"close": "IV"})
    df = px.merge(ivd, on="date", how="inner").sort_values("date")

    for w in hv_windows:
        df[f"HV{w}"] = realized_vol(df["PRICE"], window=w)

    ref = min(hv_windows, key=lambda w: abs(w - 30))
    df["Spread"] = pd.to_numeric(df["IV"], errors="coerce") - pd.to_numeric(
        df[f"HV{ref}"], errors="coerce"
    )
    df["Spread_z"] = zscore(df["Spread"], window=z_window)

    keep = (
        ["date", "PRICE", "IV"]
        + [f"HV{w}" for w in hv_windows]
        + ["Spread", "Spread_z"]
    )
    out = df[keep].dropna().reset_index(drop=True)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    atomic_write_csv(out, out_path)
    print(
        f"Wrote {out_path}  rows={len(out)}  cols={len(out.columns)}  last_date={out['date'].iloc[-1].date()}"
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--price", default="SPY")
    ap.add_argument("--iv", default="^VIX")
    ap.add_argument("--start", default="2015-01-01")
    ap.add_argument("--end", default=None)
    ap.add_argument("--out", default="data/blatality_dataset.csv")
    args = ap.parse_args()
    main(args.price, args.iv, args.start, args.end, out_path=args.out)
