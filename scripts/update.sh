#!/usr/bin/env bash
set -euo pipefail

# Use the env’s python when possible; cron will override PY below.
PY="${PY:-python3}"

# 1) Update dataset
$PY scripts/update_data.py --price SPY --iv ^VIX --start 2015-01-01 --out data/blatality_dataset.csv

# 2) Run backtest on the updated data
$PY main_backtest.py

echo "[OK] $(date) — data updated + backtest run"

# truncate log if >1MB
[ -f logs/update.log ] && [ $(wc -c < logs/update.log) -gt 1048576 ] && tail -n 1000 logs/update.log > logs/update.tmp && mv logs/update.tmp logs/update.log
