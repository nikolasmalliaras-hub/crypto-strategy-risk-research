# Results

| File | What it is |
|---|---|
| `strategies.csv` | Every backtested strategy: total return, CAGR, max drawdown, Sharpe, each calendar year, number of trades |
| `convex.csv` | Option-buying strategies, per bet: hit rate, average win, expectancy (R), drawdown at 2% risk per bet |
| `costs.csv` | Yearly result split into price, funding and costs (% of capital, simple sum of trades) |
| `correlation.csv` | Correlation of daily returns between the main strategies and BTC |
| `crash_days.csv` | Average return and correlation on BTC's worst 10% of days |
| `portfolio.csv` | Combined portfolios: equal capital vs. equal risk, with/without breakout, without options |
| `rotation.csv` | Selection-bias check for the BTC/ETH/SOL rotation |
| `backtest_v1_run.txt`, `backtest_v2_run.txt`, `analysis.txt` | Raw program output the CSVs were parsed from (original Greek labels) |

Period: 2 January 2021 to 19 October 2026. The first raw run ends on 17 October; strategies that appear in both runs give identical results.

Column meanings in the raw files: *Σύνολο* = total return, *Ετήσια* = CAGR, *Max DD* = worst drawdown, then one column per calendar year; *κλεισ.* = closed trades, *κύκλοι* = cycles, *stop* = grid restarts.
