"""Combining strategies: equal capital vs. equal risk per family, with no look-ahead.

A *family* is a group of strategies built on the same economic idea (e.g. "short volatility").
Variants of one idea share one slice of the portfolio, so five versions of the same bet do not count
as five independent bets.
"""
from __future__ import annotations

import statistics
from typing import Mapping, Optional, Sequence

Returns = Sequence[Optional[float]]


def family_returns(series: Mapping[str, Returns], families: Mapping[str, Sequence[str]]) -> dict[str, list[Optional[float]]]:
    """Equal-weighted daily return of each family (members that have not started yet are skipped)."""
    n = len(next(iter(series.values())))
    out = {}
    for fam, members in families.items():
        members = [m for m in members if m in series]
        if not members:
            continue
        col = []
        for i in range(n):
            xs = [series[m][i] for m in members if series[m][i] is not None]
            col.append(statistics.fmean(xs) if xs else None)
        out[fam] = col
    return out


def inverse_vol_weights(history: Mapping[str, Sequence[float]], min_obs: int = 20) -> Optional[dict[str, float]]:
    """Weights proportional to 1 / volatility, summing to 1. ``None`` if any input has too little history."""
    inv = {}
    for k, xs in history.items():
        if len(xs) < min_obs:
            return None
        sd = statistics.pstdev(xs)
        if sd <= 0:
            return None
        inv[k] = 1.0 / sd
    tot = sum(inv.values())
    return {k: v / tot for k, v in inv.items()}


def combine(series: Mapping[str, Returns], families: Mapping[str, Sequence[str]], mode: str = "risk",
            lookback: int = 90) -> list[Optional[float]]:
    """Daily return of the combined portfolio.

    mode="capital": every live family gets the same weight.
    mode="risk":    weights ∝ 1/volatility of each family over the previous ``lookback`` days only
                    (the current day is never used to set its own weight). Falls back to equal capital
                    until every live family has enough history.
    No leverage: weights always sum to 1.
    """
    if mode not in ("capital", "risk"):
        raise ValueError("mode must be 'capital' or 'risk'")
    fam = family_returns(series, families)
    n = len(next(iter(fam.values())))
    out: list[Optional[float]] = []
    for i in range(n):
        live = [f for f, col in fam.items() if col[i] is not None]
        if not live:
            out.append(None)
            continue
        w = None
        if mode == "risk":
            hist = {f: [x for x in fam[f][max(0, i - lookback):i] if x is not None] for f in live}
            w = inverse_vol_weights(hist)
        if w is None:
            w = {f: 1.0 / len(live) for f in live}
        out.append(sum(w[f] * fam[f][i] for f in live))
    return out
