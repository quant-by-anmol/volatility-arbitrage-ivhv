import numpy as np
import pandas as pd


def annualized_return(cum_pnl, days, trading_days=252):
    """CAGR approximation from cumulative PnL and total days."""
    total_return = cum_pnl.iloc[-1]
    years = days / trading_days
    return (1 + total_return) ** (1 / years) - 1


def annualized_volatility(pnl, trading_days=252):
    """Annualized volatility of daily PnL returns."""
    return pnl.std() * np.sqrt(trading_days)


def sharpe_ratio(pnl, risk_free_rate=0.0, trading_days=252):
    """
    Annualized Sharpe ratio assuming daily PnL series & zero RF by default.
    """
    # compute annualized return & vol
    ann_ret = pnl.mean() * trading_days
    ann_vol = pnl.std() * np.sqrt(trading_days)

    # force to scalar
    try:
        ann_vol = float(ann_vol)
    except (TypeError, ValueError):
        return np.nan

    # if zero or NaN, no Sharpe
    if ann_vol == 0.0 or np.isnan(ann_vol):
        return np.nan

    return (ann_ret - risk_free_rate) / ann_vol


def sortino_ratio(pnl, risk_free_rate=0.0, trading_days=252):
    """Annualized Sortino ratio (downside deviation only)."""
    neg_returns = pnl[pnl < 0]
    downside_vol = neg_returns.std() * np.sqrt(trading_days)
    # ensure scalar
    try:
        downside_vol = float(downside_vol)
    except (TypeError, ValueError):
        return np.nan
    if downside_vol == 0.0 or np.isnan(downside_vol):
        return np.nan
    ann_ret = pnl.mean() * trading_days
    return (ann_ret - risk_free_rate) / downside_vol


def max_drawdown(cum_pnl):
    """Maximum drawdown from cumulative PnL series."""
    running_max = cum_pnl.cummax()
    drawdowns = running_max - cum_pnl
    return drawdowns.max()


def calmar_ratio(cum_pnl, days, trading_days=252):
    """Calmar ratio = CAGR / Max drawdown."""
    ann_ret = annualized_return(cum_pnl, days, trading_days)
    mdd = max_drawdown(cum_pnl)
    # ensure scalar
    try:
        mdd = float(mdd)
    except (TypeError, ValueError):
        return np.nan
    if mdd == 0.0 or np.isnan(mdd):
        return np.nan
    return ann_ret / mdd


def compute_all_metrics(results_df):
    """
    Given `results_df` with columns:
      - 'date' (datetime)
      - 'pnl' (per-trade or per-day returns)
      - 'cum_pnl' (cumulative)
    Returns a dict of key performance metrics.
    """
    # assume results are sequential PnL per trade or per period
    pnl = results_df["pnl"]
    cum = results_df["cum_pnl"]
    days = (results_df["date"].iloc[-1] - results_df["date"].iloc[0]).days

    metrics = {
        "Total Return": cum.iloc[-1],
        "Annualized Return": annualized_return(cum, days),
        "Annualized Volatility": annualized_volatility(pnl),
        "Sharpe Ratio": sharpe_ratio(pnl),
        "Sortino Ratio": sortino_ratio(pnl),
        "Max Drawdown": max_drawdown(cum),
        "Calmar Ratio": calmar_ratio(cum, days),
        "Number of Trades": len(results_df),
        "Win Rate": (pnl > 0).mean(),
    }
    return metrics
