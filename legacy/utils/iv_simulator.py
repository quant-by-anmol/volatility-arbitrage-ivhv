import numpy as np
import pandas as pd


def simulate_implied_volatility(hv_series, mode="random", low=0.5, high=1.5):
    """
    Simulates implied volatility (IV) as a multiple of HV.

    Parameters:
    - hv_series: pd.Series of historical vol
    - mode: "random" or "fixed"
    - low, high: range of multipliers if random

    Returns:
    - pd.Series of simulated IV
    """
    if mode == "random":
        multipliers = np.random.uniform(low, high, len(hv_series))
    elif mode == "fixed":
        multipliers = np.full(len(hv_series), (low + high) / 2)
    else:
        raise ValueError("Invalid mode. Use 'random' or 'fixed'.")

    iv = hv_series * multipliers
    return pd.Series(iv, index=hv_series.index)
