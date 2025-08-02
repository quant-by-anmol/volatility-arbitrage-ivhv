import pandas as pd


def generate_volatility_signals(
    iv_series, hv_series, upper_thresh=1.1, lower_thresh=0.7
):
    """
    Compares IV/HV and generates buy/sell/hold signals.

    Parameters:
    - iv_series: pd.Series of simulated implied volatility
    - hv_series: pd.Series of historical volatility
    - upper_thresh: threshold to sell vol (IV >> HV)
    - lower_thresh: threshold to buy vol (IV << HV)

    Returns:
    - pd.Series of 'Buy', 'Sell', or 'Hold'
    """
    ratio = iv_series / hv_series
    signal = pd.Series("Hold", index=ratio.index)

    signal[ratio > upper_thresh] = "Sell"
    signal[ratio < lower_thresh] = "Buy"

    return signal
