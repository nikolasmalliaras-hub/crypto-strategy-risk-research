"""Performance and risk metrics on a daily return series.

All functions take plain sequences of daily simple returns (0.01 = +1%). ``None`` marks a day before
the series starts and is skipped. Only the standard library is needed.
"""
from __future__ import annotations

import math
import statistics
from typing import Iterable, Optional, Sequence

TRADING_DAYS = 365  # crypto trades every day


def _clean(returns: Iterable[Optional[float]]) -> list[float]:
    return [r for r in returns if r is not None]


def equity_curve(returns: Iterable[Optional[float]], start: float = 1.0) -> list[float]:
    """Compounded equity, one point per non-missing return."""
    e, out = start, []
    for r in _clean(returns):
        e *= 1.0 + r
        out.append(e)
    return out


def total_return(returns: Iterable[Optional[float]]) -> float:
    curve = equity_curve(returns)
    return curve[-1] - 1.0 if curve else 0.0


def cagr(returns: Sequence[Optional[float]]) -> float:
    """Compound annual growth rate."""
    xs = _clean(returns)
    if not xs:
        return 0.0
    growth = 1.0 + total_return(xs)
    if growth <= 0:
        return -1.0
    return growth ** (TRADING_DAYS / len(xs)) - 1.0


def max_drawdown(returns: Iterable[Optional[float]]) -> float:
    """Worst peak-to-trough fall of the compounded equity (a negative number)."""
    peak, worst = 1.0, 0.0
    for e in equity_curve(returns):
        peak = max(peak, e)
        worst = min(worst, e / peak - 1.0)
    return worst


def annual_volatility(returns: Iterable[Optional[float]]) -> float:
    xs = _clean(returns)
    return statistics.pstdev(xs) * math.sqrt(TRADING_DAYS) if len(xs) > 1 else 0.0


def sharpe(returns: Iterable[Optional[float]], risk_free: float = 0.0) -> float:
    """Annualised Sharpe ratio of daily returns (risk-free rate given per year)."""
    xs = [r - risk_free / TRADING_DAYS for r in _clean(returns)]
    if len(xs) < 2:
        return 0.0
    sd = statistics.pstdev(xs)
    return statistics.fmean(xs) / sd * math.sqrt(TRADING_DAYS) if sd > 0 else 0.0


def sortino(returns: Iterable[Optional[float]]) -> float:
    """Like Sharpe, but only downside days count as risk."""
    xs = _clean(returns)
    down = [min(0.0, r) for r in xs]
    dd = math.sqrt(sum(d * d for d in down) / len(down)) if down else 0.0
    return statistics.fmean(xs) / dd * math.sqrt(TRADING_DAYS) if dd > 0 else 0.0


def expected_shortfall(returns: Iterable[Optional[float]], level: float = 0.05) -> float:
    """Average of the worst ``level`` share of days (historical CVaR, a negative number)."""
    xs = sorted(_clean(returns))
    if not xs:
        return 0.0
    k = max(1, int(len(xs) * level))
    return statistics.fmean(xs[:k])


def calendar_returns(dates: Sequence, returns: Sequence[Optional[float]]) -> dict[int, float]:
    """{year: return} from aligned sequences of dates (anything with ``.year``) and daily returns."""
    by: dict[int, list[float]] = {}
    for d, r in zip(dates, returns):
        if r is not None:
            by.setdefault(d.year, []).append(r)
    return {y: total_return(rs) for y, rs in sorted(by.items())}


def summary(returns: Sequence[Optional[float]]) -> dict[str, float]:
    return dict(total=total_return(returns), cagr=cagr(returns), max_drawdown=max_drawdown(returns),
                volatility=annual_volatility(returns), sharpe=sharpe(returns), sortino=sortino(returns),
                es_5pct=expected_shortfall(returns))
