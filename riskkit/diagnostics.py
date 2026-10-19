"""Diagnostics: where a strategy's result comes from, and how it behaves when the market breaks."""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from typing import Mapping, Optional, Sequence

Returns = Sequence[Optional[float]]


def correlation(a: Returns, b: Returns, min_obs: int = 30) -> Optional[float]:
    """Pearson correlation over the days where both series exist."""
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(pairs) < min_obs:
        return None
    xs, ys = zip(*pairs)
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if not sx or not sy:
        return None
    return sum((x - mx) * (y - my) for x, y in pairs) / (sx * sy)


def correlation_matrix(series: Mapping[str, Returns]) -> dict[str, dict[str, Optional[float]]]:
    names = list(series)
    return {a: {b: (1.0 if a == b else correlation(series[a], series[b])) for b in names} for a in names}


def stress_days(benchmark: Returns, share: float = 0.10) -> list[bool]:
    """Mask of the benchmark's worst ``share`` of days (e.g. BTC's worst 10% days)."""
    xs = sorted(x for x in benchmark if x is not None)
    if not xs:
        return [False] * len(benchmark)
    cut = xs[max(0, int(len(xs) * share) - 1)]
    return [x is not None and x <= cut for x in benchmark]


@dataclass
class StressStats:
    mean_return: Optional[float]      # average daily return on stress days
    correlation: Optional[float]      # correlation with the benchmark on those days only
    hit_rate: Optional[float]         # share of stress days the strategy made money


def stress_behaviour(strategy: Returns, benchmark: Returns, share: float = 0.10) -> StressStats:
    """How a strategy behaves on the benchmark's worst days."""
    mask = stress_days(benchmark, share)
    xs = [s for s, m in zip(strategy, mask) if m and s is not None]
    if not xs:
        return StressStats(None, None, None)
    c = correlation([s if m else None for s, m in zip(strategy, mask)], [b if m else None for b, m in zip(benchmark, mask)], min_obs=10)
    return StressStats(statistics.fmean(xs), c, sum(1 for x in xs if x > 0) / len(xs))


@dataclass
class CostSplit:
    price: float       # P&L from price moves, % of capital per year
    funding: float     # funding received (+) or paid (−)
    costs: float       # fees + slippage (negative)

    @property
    def gross(self) -> float:
        return self.price + self.funding

    @property
    def net(self) -> float:
        return self.price + self.funding + self.costs

    def verdict(self) -> str:
        """Plain-language reading of the split."""
        if self.net > 0:
            return "positive after costs"
        if self.gross <= 0:
            return "negative even before costs (no premium to harvest)"
        return "positive before costs, consumed by costs (trade less / cheaper)"


def cost_split(trades: Sequence[Mapping[str, float]], years: float) -> CostSplit:
    """Aggregate per-trade results (keys: price, funding, costs, as fractions of capital) into yearly figures."""
    years = max(years, 1e-9)
    return CostSplit(price=sum(t["price"] for t in trades) / years, funding=sum(t["funding"] for t in trades) / years,
                     costs=-abs(sum(t["costs"] for t in trades)) / years)
