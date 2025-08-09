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


# utils/strategy_rules.py  (append)
def generate_vol_spread_signals(df, z_hi=1.5, z_lo=-1.5, dedupe=True):
    """
    IV-HV divergence signals off z-score.
    SELL_VOL when z >= z_hi, BUY_VOL when z <= z_lo, else NEUTRAL.
    """
    s = df["z"].astype(float)
    sig = s.apply(
        lambda v: "SELL_VOL" if v >= z_hi else ("BUY_VOL" if v <= z_lo else "NEUTRAL")
    )
    out = df.copy()
    out["signal"] = sig
    if dedupe:
        out["signal_compact"] = out["signal"].where(
            out["signal"].ne(out["signal"].shift())
        )
    return out
