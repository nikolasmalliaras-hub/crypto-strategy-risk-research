"""Execution realism: intrabar price paths, trading costs and approximate option quotes.

These are the pieces that make a backtest honest. They are generic and contain no strategy logic.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# ---------------------------------------------------------------- intrabar path


def intrabar_path(o: float, h: float, l: float, c: float, steps: int = 12) -> list[float]:
    """Prices at ``steps`` evenly spaced moments inside one OHLC bar (the last one is the close).

    The path is open → first extreme → second extreme → close. In a bar that closed up the low comes
    first, otherwise the high comes first. Stops and targets are then checked against the wick and not
    only against the close. ``steps`` must be a multiple of 3 so both extremes are hit exactly.
    """
    if steps % 3:
        raise ValueError("steps must be a multiple of 3")
    a, b = (l, h) if c >= o else (h, l)
    knots = (o, a, b, c)
    out = []
    for k in range(1, steps + 1):
        f = k / steps * 3
        seg = min(2, int(f))
        w = f - seg
        out.append(knots[seg] + (knots[seg + 1] - knots[seg]) * w)
    return out


# ---------------------------------------------------------------- costs


@dataclass(frozen=True)
class CostModel:
    taker_fee: float = 0.00045          # per side
    spike_multiplier: float = 1.5        # slippage after a volume spike
    tiers: tuple = ((5e8, 0.0001), (1e8, 0.0002), (2e7, 0.0005), (5e6, 0.0010), (0.0, 0.0020))  # (24h volume ≥, slippage)

    def slippage(self, volume_24h: float, spike: bool = False) -> float:
        s = next(sl for v, sl in self.tiers if volume_24h >= v)
        return s * (self.spike_multiplier if spike else 1.0)

    def one_side(self, volume_24h: float, spike: bool = False) -> float:
        """Cost of one fill as a fraction of notional (fee + slippage)."""
        return self.taker_fee + self.slippage(volume_24h, spike)

    def round_trip(self, volume_24h: float, spike: bool = False) -> float:
        return 2.0 * self.one_side(volume_24h, spike)


def funding_cost(notional_side: int, annual_rate: float, hours: float) -> float:
    """Funding paid (+) by a position over ``hours``; side +1 = long, −1 = short.
    Longs pay when the rate is positive."""
    return notional_side * annual_rate * hours / (24 * 365)


# ---------------------------------------------------------------- option quotes (approximation)


def _ncdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def black_scholes(forward: float, strike: float, vol: float, years: float, kind: str) -> float:
    """Undiscounted Black-76 price of a call ('C') or put ('P')."""
    if years <= 0 or vol <= 0:
        return max(0.0, forward - strike) if kind == "C" else max(0.0, strike - forward)
    sd = vol * math.sqrt(years)
    d1 = (math.log(forward / strike) + sd * sd / 2) / sd
    d2 = d1 - sd
    if kind == "C":
        return forward * _ncdf(d1) - strike * _ncdf(d2)
    return strike * _ncdf(-d2) - forward * _ncdf(-d1)


def bs_delta(forward: float, strike: float, vol: float, years: float, kind: str) -> float:
    if years <= 0 or vol <= 0:
        return (1.0 if forward > strike else 0.0) if kind == "C" else (-1.0 if forward < strike else 0.0)
    d1 = (math.log(forward / strike) + vol * vol * years / 2) / (vol * math.sqrt(years))
    return _ncdf(d1) if kind == "C" else _ncdf(d1) - 1.0


@dataclass(frozen=True)
class QuoteModel:
    """Reconstructs a bid/ask for an option when no historical option prices exist.

    Implied volatility = an index such as Deribit DVOL (no smile, one IV for every expiry), plus a
    proportional half-spread and one exchange tick. This is an approximation: real out-of-the-money
    puts trade at a higher IV, so premium *sold* is overstated and premium *bought* is understated.
    """
    half_spread: float = 0.025
    tick: float = 0.0001                 # in units of the underlying (Deribit quotes in coin)
    fee_rate: float = 0.0003             # of the underlying, capped at 12.5% of the option price

    def quote(self, forward: float, strike: float, iv: float, years: float, kind: str) -> tuple[float, float]:
        mid = max(0.0, black_scholes(forward, strike, iv, years, kind)) / forward
        bid = max(0.0, mid * (1 - self.half_spread) - self.tick)
        ask = mid * (1 + self.half_spread) + self.tick
        return bid * forward, ask * forward

    def fee(self, price: float, underlying: float) -> float:
        return min(self.fee_rate * underlying, 0.125 * price)
