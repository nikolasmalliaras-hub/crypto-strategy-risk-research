# Methodology

How the backtest is built, and every assumption that could make it look better or worse than reality.

## 1. One engine, two modes

The strategies are written once and run unchanged in two places:

- **Live paper trading.** A read-only monitoring application runs them every minute on Hyperliquid and Deribit market data. No orders are sent and there are no exchange keys.
- **Backtest.** A replay harness imports the **same strategy code** and swaps only the data layer: clock, candles, funding and option quotes. Every database is redirected to a scratch folder.

So the backtest tests the code that actually runs, not a simplified copy of it. The strategy code itself is private. This repository publishes the method, the generic building blocks ([`riskkit`](../riskkit)) and the results.

## 2. Data (all free, no account needed)

| Data | Source | Used for |
|---|---|---|
| 1-hour OHLCV, 65 large coins, Jun 2020 → today | Binance USDT-M futures (`data.binance.vision` monthly files + API for the current month) | Prices, volume, volatility |
| Funding rates | Binance USDT-M futures | Funding paid / received every hour |
| 1-minute OHLCV for BTC, ETH, SOL | Binance USDT-M futures | The wick-reversion strategy |
| DVOL (30-day implied volatility index), BTC & ETH, Mar 2021 → today | Deribit public API | Option prices (see §6) |

Binance volume is several times Hyperliquid's. It is scaled by ×0.2, so the same liquidity thresholds and slippage tiers apply as in the live app.

## 3. Time and look-ahead

- The replay runs on a fake clock. At time *t* a strategy sees only candles that **closed** before *t*.
- **Intrabar path (wicks).** Each hour is replayed in **12 steps of 5 minutes** along *open → first extreme → second extreme → close*. If the candle closed above its open, the low comes first; otherwise the high comes first. Stops, targets, trailing stops, liquidations, grid fills and breakout triggers all see the wicks, not just the closes.
- Inside the hour only open positions are managed. **New entries happen only at the hourly close**, using the previous closed bar's statistics, so a strategy never "knows" the full hour's volume before it has happened. Breakout orders and options are the exception, because they are resting orders in real life too.
- Portfolio weights (see §7) use only the previous 90 days.

## 4. Costs

The same cost model as the live app:

| Cost | Model |
|---|---|
| Perp fees | 0.045% taker per side |
| Slippage | 0.01% – 0.20% per side by 24h volume, ×1.5 right after a volume spike |
| Funding | Accrued hourly from the actual historical rate; longs pay positive funding |
| Option fees | Deribit: min(0.03% of the underlying, 12.5% of the option price); 0.015% at delivery |
| Option spread | Bid/ask = model price ∓ 2.5% ∓ 1 tick |
| Grid fills | 0.015% maker |

A sanity check is built in: the **random basket** (5 random longs / 5 random shorts every week) loses about −13% a year. That is roughly what trading costs alone should cost such a basket.

## 5. Guarding against luck and over-fitting

- **Placebo benchmark.** Every strategy is compared with the random basket. In live tracking, a strategy is only flagged as significant when its t-statistic against the placebo clears a **Bonferroni-corrected** threshold for the number of strategies tested at once.
- **Revisions decided in advance.** Each revised (v2) strategy got **one** new rule set, written down from first principles before its backtest was run: fewer trades, liquid coins only, volatility-scaled stops, trailing stops only once in profit. There was no parameter search.
- **Hold-out year.** 2026 was not used to design any rule. It is reported separately as the most honest number.
- **Failures are reported.** Every strategy that was tested is in the results, including the ones that lost everything.

## 6. Options: an approximation

There is no free history of Deribit option prices. Option quotes are therefore **reconstructed**:

- price = Black-Scholes on the perp price, with implied volatility = DVOL at that hour;
- the strike grid and expiries (dailies plus Fridays) mimic Deribit;
- settlement at the 08:00 UTC price.

This is the weakest part of the backtest:

- **No smile.** Real out-of-the-money puts trade at a higher IV than DVOL, so strangles and wings are priced too cheaply.
- **One volatility for every expiry.** DVOL is a 30-day index, but it is used for 1-day and 7-day options too.
- **Hourly delta hedging** instead of every minute.

Short-volatility results are therefore probably **optimistic**. The live paper strategies are the real test.

## 7. Portfolio construction

The portfolio study ([`riskkit.portfolio`](../riskkit/portfolio.py)) combines the daily returns of the strategies that survived:

- **Families:** short volatility (daily and weekly short gamma), BTC + options (covered call and collar), long volatility (14-day strangle), and trend (Trend 10).
- **Equal risk:** each family gets weight ∝ 1 / (its daily volatility over the previous 90 days). Inside a family, the strategies are equally weighted.
- No leverage, daily rebalancing. Rebalancing costs *between* strategies are not modelled. They are small next to the strategies' own costs.

**Important:** the members of the portfolio were chosen **after** seeing the full backtest, 2026 included. The portfolio result is therefore in-sample. Forward paper trading is the real test.

## 8. Known limitations

| Limitation | Direction of bias |
|---|---|
| Universe = coins that exist today (survivorship) | Flatters long strategies |
| Options priced without smile; one IV for all expiries | Flatters short-vol, mis-states long-vol |
| Portfolio members chosen after seeing the results | Flatters the portfolio |
| Fast strategies enter at the hourly close (live: within a minute) | Slightly hurts momentum-style strategies |
| Binance wicks are smaller than Hyperliquid's | Hurts the wick strategy |
| No history of open interest, liquidations, trader positions or the option smile | Those strategies are measured live only |
