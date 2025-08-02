import numpy as np
import pandas as pd


def calculate_historical_volatility(price_series, window=20, annualization_factor=252):
    """
    Calculate rolling historical volatility (HV) based on log returns.

    Parameters:
    - price_series: pd.Series of prices (e.g., NIFTY close)
    - window: number of days for rolling std dev
    - annualization_factor: 252 for daily data

    Returns:
    - pd.Series of HV values
    """
    log_returns = np.log(price_series / price_series.shift(1))
    rolling_std = log_returns.rolling(window=window).std()
    hv = rolling_std * np.sqrt(annualization_factor)

    return hv
