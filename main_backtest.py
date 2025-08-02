import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils.hv_calculator import calculate_historical_volatility
from utils.iv_simulator import simulate_implied_volatility
from utils.payoff_calculator import simulate_straddle_payoff
from utils.performance_metrics import compute_all_metrics
from utils.strategy_rules import generate_volatility_signals

np.random.seed(42)
from utils.performance_metrics import annualized_volatility, compute_all_metrics

TARGET_ANN_VOL = 0.25  # 25% target annual vol


# ----------- 1. Load Data -------------------
df = pd.read_csv("data/spot_data.csv", parse_dates=["Date"])
df.set_index("Date", inplace=True)
close_prices = df["Close"]

# ----------- 2. Compute HV and Simulate IV ------------
hv_20 = calculate_historical_volatility(close_prices, window=20)
iv_sim = simulate_implied_volatility(hv_20, mode="random")

# ----------- 3. Generate Signals -------------
signals = generate_volatility_signals(iv_sim, hv_20)

# ----------- 4. Simulate PnL ---------------
results = simulate_straddle_payoff(
    price_series=close_prices,
    signals=signals,
    hold_period=5,
    premium_pct=0.03,  # if you’re still using mock IV
    commission_pct=0.001,  # 0.1% round-trip
    slippage_pct=0.0005,  # 0.05% per leg
    stop_loss_pct=1.5,  # allow full premium loss before stop
    profit_target_pct=0.05,
)

results["cum_pnl"] = results["pnl"].cumsum()
# ─── Scale PnL to Target Annual Volatility ───────────────────
current_ann_vol = annualized_volatility(results["pnl"])
scale_factor = TARGET_ANN_VOL / current_ann_vol
print(f"🔧 Scaling factor to reach {TARGET_ANN_VOL*100:.0f}% vol: {scale_factor:.6f}")

# Apply scaling
results["pnl_scaled"] = results["pnl"] * scale_factor
results["cum_pnl_scaled"] = results["pnl_scaled"].cumsum()

# Compute scaled metrics
scaled_df = results.rename(columns={"pnl_scaled": "pnl", "cum_pnl_scaled": "cum_pnl"})[
    ["date", "pnl", "cum_pnl"]
]
metrics_scaled = compute_all_metrics(scaled_df)

# Scale PnL so that annualized volatility ≈ TARGET_ANN_VOL
current_ann_vol = annualized_volatility(results["pnl"])
scale_factor = TARGET_ANN_VOL / current_ann_vol
print(f"🔧 Scaling factor to reach {TARGET_ANN_VOL*100:.0f}% vol: {scale_factor:.6f}")

# apply scaling
results["pnl_scaled"] = results["pnl"] * scale_factor
results["cum_pnl_scaled"] = results["pnl_scaled"].cumsum()

# compute scaled metrics
scaled_df = results.rename(columns={"pnl_scaled": "pnl", "cum_pnl_scaled": "cum_pnl"})[
    ["date", "pnl", "cum_pnl"]
]
metrics_scaled = compute_all_metrics(scaled_df)

# ----------- 5. Plot Equity Curve ----------
plt.figure(figsize=(12, 6))
plt.plot(results["date"], results["cum_pnl"], label="Equity Curve", color="purple")
plt.title("Cumulative PnL from IV-HV Divergence Strategy")
plt.grid()
plt.legend()
plt.tight_layout()
plt.savefig("outputs/equity_curve.png")
# plt.show()

print("✅ Backtest complete. Calculating stats...")

# ——— Compute & Save Metrics ————————————
metrics = compute_all_metrics(results)

with open("outputs/strategy_stats.txt", "w") as f:
    for name, val in metrics.items():
        if isinstance(val, float):
            f.write(f"{name:22}: {val:.4f}\n")
        else:
            f.write(f"{name:22}: {val}\n")

# ——— Print Summary to Console ——————————
print("\n📊 Performance Metrics")
for name, val in metrics.items():
    if isinstance(val, float):
        print(f"{name:22}: {val:.4f}")
    else:
        print(f"{name:22}: {val}")

results.to_csv("outputs/trades_summary.csv", index=False)

# import itertools

# import pandas as pd

# # ─── FULL PARAM GRID ─────────────────────────────────────────
# upper_list = [1.1, 1.2, 1.3]
# lower_list = [0.6, 0.7, 0.8]
# stop_list = [0.5, 1.0, 1.5]
# profit_target_list = [0.05, 0.1, 0.2]

# records = []
# for upper, lower, stop, profit in itertools.product(
#     upper_list, lower_list, stop_list, profit_target_list
# ):

#     sigs = generate_volatility_signals(
#         iv_sim, hv_20, upper_thresh=upper, lower_thresh=lower
#     )

#     trades = simulate_straddle_payoff(
#         price_series=close_prices,
#         signals=sigs,
#         hold_period=5,
#         premium_pct=0.03,
#         commission_pct=0.001,
#         slippage_pct=0.0005,
#         stop_loss_pct=stop,
#         profit_target_pct=profit,
#     )
#     trades["cum_pnl"] = trades["pnl"].cumsum()
#     m = compute_all_metrics(trades)

#     records.append(
#         {
#             "upper": upper,
#             "lower": lower,
#             "stop_loss_pct": stop,
#             "profit_target_pct": profit,
#             "Sharpe": m["Sharpe Ratio"],
#             "TotalRet": m["Total Return"],
#             "MaxDraw": m["Max Drawdown"],
#             "WinRate": m["Win Rate"],
#         }
#     )

# grid_df = pd.DataFrame(records)
# grid_df.to_csv("outputs/param_grid_full.csv", index=False)
# print("✅ Full grid search complete. See outputs/param_grid_full.csv")
