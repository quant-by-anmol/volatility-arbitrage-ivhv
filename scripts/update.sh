#!/usr/bin/env bash
set -euo pipefail

# Use the env’s python when possible; cron will override PY below.
PY="${PY:-python3}"

# 1) Update dataset
$PY scripts/update_data.py --price SPY --iv ^VIX --start 2015-01-01 --out data/blatality_dataset.csv

# 2) Run backtest on the updated data
$PY main_backtest.py

echo "[OK] $(date) — data updated + backtest run"
