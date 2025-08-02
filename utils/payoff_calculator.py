import pandas as pd


def simulate_straddle_payoff(
    price_series,
    signals,
    hold_period=5,
    premium_pct=None,
    premium_series=None,
    commission_pct=0.001,
    slippage_pct=0.0005,
    stop_loss_pct=1.0,
    profit_target_pct=1.0,
):
    """
    Simulates straddle PnL with:
      - commission & slippage
      - stop-loss at -stop_loss_pct * premium
      - profit-take at +profit_target_pct * premium

    Exits as soon as PnL hits either threshold, or at hold_period.

    Args:
      price_series (pd.Series): index=date, values=spot price
      signals (pd.Series): 'Buy' / 'Sell' / 'Hold'
      hold_period (int): max days to hold
      premium_pct (float): flat % premium if premium_series is None
      premium_series (pd.Series): real premium per date (optional)
      commission_pct (float): round-trip commission rate
      slippage_pct (float): per-leg slippage rate
      stop_loss_pct (float): fraction of premium to allow as max loss
      profit_target_pct (float): fraction of premium to lock in profit

    Returns:
      pd.DataFrame of trades with columns:
        date, signal, entry_price, exit_price, days_held,
        premium, commission, slippage, pnl
    """

    trades = []
    dates = price_series.index
    print(
        f">>> simulate_straddle_payoff called with profit_target_pct = {profit_target_pct}"
    )

    for i, date in enumerate(dates):
        sig = signals.loc[date]
        if sig == "Hold":
            continue

        entry_price = price_series.iloc[i]
        premium = (
            premium_series.loc[date]
            if premium_series is not None
            else entry_price * premium_pct
        )
        commission = entry_price * commission_pct * 2
        slippage = entry_price * slippage_pct * 2
        max_loss = -premium * stop_loss_pct
        target_win = premium * profit_target_pct

        pnl = None
        days = 0
        # simulate each day until threshold or hold_period
        for days in range(1, hold_period + 1):
            if i + days >= len(dates):
                break
            exit_price = price_series.iloc[i + days]
            move = abs(exit_price - entry_price)
            raw = (move - premium) if sig == "Buy" else (premium - move)
            net = raw - commission - slippage

            # profit-take
            if net >= target_win:
                pnl = net
                break

            # stop-loss
            if net <= max_loss:
                pnl = net
                break

        # if neither triggered, exit at hold_period
        if pnl is None:
            exit_price = price_series.iloc[min(i + hold_period, len(dates) - 1)]
            move = abs(exit_price - entry_price)
            raw = (move - premium) if sig == "Buy" else (premium - move)
            pnl = raw - commission - slippage

        trades.append(
            {
                "date": date,
                "signal": sig,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "days_held": days,
                "premium": premium,
                "commission": commission,
                "slippage": slippage,
                "pnl": pnl,
            }
        )

    return pd.DataFrame(trades)
