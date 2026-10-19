"""
Self-contained demo of riskkit on synthetic data (no downloads needed):

  * four toy "strategy families" with very different risk profiles,
  * how they behave on the market's worst days,
  * equal capital vs. equal risk,
  * why stops must be checked against the wick and not only the close.

    python examples/demo.py
"""
import os
import random
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from riskkit import diagnostics, execution, metrics, portfolio  # noqa: E402

rng = random.Random(7)
N = 365 * 5
days = [date(2021, 1, 1) + timedelta(days=i) for i in range(N)]

# a market with fat tails and occasional crashes
market = []
for _ in range(N):
    r = rng.gauss(0.0022, 0.03)
    if rng.random() < 0.004:
        r -= rng.uniform(0.08, 0.15)
    market.append(r)

# toy families (illustrative only)
short_vol = [0.0006 - 0.12 * max(0.0, abs(m) - 0.05) + rng.gauss(0, 0.003) for m in market]      # earns a premium, loses on big moves (capped)
trend = [(0.4 if sum(market[max(0, i - 20):i]) > 0 else -0.4) * m + rng.gauss(0, 0.004) for i, m in enumerate(market)]  # follows the last 20 days
long_vol = [-0.0004 + 0.10 * max(0.0, abs(m) - 0.05) + rng.gauss(0, 0.003) for m in market]      # pays a premium, gains on big moves
btc_options = [0.8 * m + 0.0004 + rng.gauss(0, 0.004) for m in market]                          # long the market, with an income overlay

series = {"short_vol": short_vol, "trend": trend, "long_vol": long_vol, "btc_options": btc_options}
families = {"Short vol": ["short_vol"], "Trend": ["trend"], "Long vol": ["long_vol"], "BTC + options": ["btc_options"]}


def line(name, r):
    s = metrics.summary(r)
    print(f"{name:<24}{s['cagr'] * 100:>+8.1f}%{s['max_drawdown'] * 100:>+9.1f}%{s['sharpe']:>8.2f}{s['es_5pct'] * 100:>+10.2f}%")


print(f"{'':<24}{'CAGR':>9}{'Max DD':>10}{'Sharpe':>8}{'ES 5%':>11}")
for k, v in series.items():
    line(k, v)
line("market", market)
print()
line("Equal capital", portfolio.combine(series, families, "capital"))
line("Equal risk", portfolio.combine(series, families, "risk"))

print("\nOn the market's worst 10% of days:")
for k, v in series.items():
    st = diagnostics.stress_behaviour(v, market)
    print(f"  {k:<14} avg {st.mean_return * 100:+.2f}%/day   corr {st.correlation:+.2f}   up on {st.hit_rate * 100:.0f}% of them")

print("\nCalendar years, equal risk:", {y: f"{r * 100:+.1f}%" for y, r in metrics.calendar_returns(days, portfolio.combine(series, families, "risk")).items()})

# wicks: a long with a 3% stop, in a bar that closes up but wicks −5% first
o, h, l, c = 100.0, 104.0, 95.0, 103.0
path = execution.intrabar_path(o, h, l, c)
hit = next((p for p in path if p <= 97.0), None)
print(f"\nBar O {o} H {h} L {l} C {c}: close-only check says the 97 stop survives; the intrabar path hits it at {hit:.2f}.")

cm = execution.CostModel()
print(f"Round-trip cost, $1B/day coin: {cm.round_trip(1e9) * 100:.3f}% · $10M/day coin after a spike: {cm.round_trip(1e7, spike=True) * 100:.3f}%")
