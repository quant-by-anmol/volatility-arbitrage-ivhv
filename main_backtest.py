# main_backtest.py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils.data_loader import load_market_data
from utils.performance_metrics import compute_all_metrics  # reuse your metrics
from utils.strategy_rules import generate_vol_spread_signals

OUT_TRADES = "outputs/trades_summary.csv"
OUT_STATS = "outputs/strategy_stats.txt"
OUT_EQUITY = "outputs/equity_curve.png"

Z_HI = 1.5  # thresholds you can tune later
Z_LO = -1.5


def backtest(df: pd.DataFrame) -> pd.DataFrame:
    """
    Proxy backtest using spot returns:
      SELL_VOL -> 50% exposure (hedged), else 100%.
    This is a clean, fast narrative until you wire real options PnL.
    """
    out = df.copy()
    out["ret"] = np.log(out["spot"]).diff()
    weight = np.where(out["signal"] == "SELL_VOL", 0.5, 1.0)
    out["pnl"] = weight * out["ret"]  # name as 'pnl' for your metrics fn
    out["cum_pnl"] = out["pnl"].cumsum()  # cum log-return
    out["equity"] = np.exp(out["cum_pnl"])  # equity curve for plotting
    return out


def save_equity_plot(df_bt: pd.DataFrame):
    plt.figure(figsize=(10, 4))
    plt.plot(df_bt["date"], df_bt["equity"])
    plt.title("Blatality Strategy Equity (proxy)")
    plt.tight_layout()
    plt.savefig(OUT_EQUITY, dpi=150)


def main():
    df = load_market_data("data/blatality_dataset.csv")
    df = generate_vol_spread_signals(df, z_hi=Z_HI, z_lo=Z_LO, dedupe=True)

    df_bt = backtest(df)

    # Outputs consistent with your repo
    df_bt[
        ["date", "spot", "iv", "z", "signal", "signal_compact", "pnl", "cum_pnl"]
    ].to_csv(OUT_TRADES, index=False)
    save_equity_plot(df_bt)

    # Metrics: reuse your function over the pnl series
    metrics = compute_all_metrics(
        df_bt[["date", "pnl", "cum_pnl"]].rename(
            columns={"pnl": "pnl", "cum_pnl": "cum_pnl"}
        )
    )
    with open(OUT_STATS, "w") as f:
        for k, v in metrics.items():
            f.write(f"{k}: {v}\n")

    print("Wrote:", OUT_TRADES, OUT_STATS, OUT_EQUITY)
    print(df_bt[["date", "z", "signal"]].tail(1).to_string(index=False))


if __name__ == "__main__":
    main()
