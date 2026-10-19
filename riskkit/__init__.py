"""riskkit — small, dependency-free toolkit for measuring strategy risk honestly.

    metrics      CAGR, drawdown, Sharpe, Sortino, expected shortfall, calendar returns
    portfolio    equal-capital vs. equal-risk (inverse-volatility) combination per family, no look-ahead
    diagnostics  correlation, behaviour on stress days, cost decomposition
    execution    intrabar OHLC paths, a volume-tiered cost model, approximate option quotes
"""
from . import diagnostics, execution, metrics, portfolio  # noqa: F401

__all__ = ["metrics", "portfolio", "diagnostics", "execution"]
__version__ = "1.0.0"
