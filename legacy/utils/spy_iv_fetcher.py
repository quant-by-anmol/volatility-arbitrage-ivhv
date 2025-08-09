import datetime
import os

import pandas as pd
import yfinance as yf

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def fetch_spy_atm_iv_premium(as_of_date=None):
    """
    Fetches SPY’s ATM implied vol and premium for the nearest expiry.
    Caches daily results under data/parsed_iv_data/spy_iv_YYYY-MM-DD.csv
    """
    # 1. Date
    today = as_of_date or datetime.date.today()
    date_str = today.strftime("%Y-%m-%d")

    # 2. Check cache
    cache_dir = os.path.join(BASE_PATH, "data", "parsed_iv_data")
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"spy_iv_{date_str}.csv")
    if os.path.exists(cache_path):
        return pd.read_csv(cache_path, index_col=0, parse_dates=True)

    # 3. Fetch underlying & expiries
    ticker = yf.Ticker("SPY")
    spot = ticker.history(start=date_str, end=date_str).Close.iloc[-1]
    expiries = ticker.options
    if not expiries:
        raise Exception("No expiries found for SPY")

    # 4. Use the nearest expiry after as_of_date
    expiry_dates = [datetime.datetime.strptime(e, "%Y-%m-%d").date() for e in expiries]
    expiry = min((e for e in expiry_dates if e >= today), default=expiry_dates[0])
    chain = ticker.option_chain(expiry.strftime("%Y-%m-%d"))
    calls, puts = chain.calls, chain.puts

    # 5. Find ATM strike
    strikes = calls["strike"]
    atm = strikes.iloc[(abs(strikes - spot)).argmin()]

    ce = calls[calls["strike"] == atm].iloc[0]
    pe = puts[puts["strike"] == atm].iloc[0]

    # 6. Build df & cache
    df = pd.DataFrame(
        [
            {
                "date": date_str,
                "spot": spot,
                "atm_strike": atm,
                "ce_iv": ce["impliedVolatility"],
                "pe_iv": pe["impliedVolatility"],
                "ce_price": ce["lastPrice"],
                "pe_price": pe["lastPrice"],
            }
        ]
    ).set_index("date")
    df.to_csv(cache_path)
    print(f"✅ SPY IV+premium saved to {cache_path}")
    return df
