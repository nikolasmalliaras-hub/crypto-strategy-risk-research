import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from riskkit import diagnostics, execution, metrics, portfolio  # noqa: E402


def test_drawdown_and_total():
    r = [0.10, -0.50, 0.20]
    assert math.isclose(metrics.total_return(r), 1.1 * 0.5 * 1.2 - 1)
    assert math.isclose(metrics.max_drawdown(r), -0.5)
    assert metrics.max_drawdown([0.01] * 10) == 0.0


def test_missing_days_are_skipped():
    assert metrics.total_return([None, 0.1, None]) == metrics.total_return([0.1])


def test_intrabar_path_hits_both_extremes_and_ends_at_close():
    p = execution.intrabar_path(100, 110, 90, 105)
    assert min(p) == 90 and max(p) == 110 and p[-1] == 105
    assert p.index(90) < p.index(110)            # up bar: low first
    q = execution.intrabar_path(100, 110, 90, 95)
    assert q.index(110) < q.index(90)            # down bar: high first


def test_inverse_vol_weights_sum_to_one_and_favour_calm():
    w = portfolio.inverse_vol_weights({"calm": [0.01, -0.01] * 20, "wild": [0.05, -0.05] * 20})
    assert math.isclose(sum(w.values()), 1.0)
    assert w["calm"] > w["wild"]


def test_risk_weights_use_only_the_past():
    a = [0.01, -0.01] * 60
    b = [0.02, -0.02] * 60
    base = portfolio.combine({"a": a, "b": b}, {"A": ["a"], "B": ["b"]}, "risk")
    b2 = b[:] ; b2[-1] = 0.5                      # change only the future (last day)
    moved = portfolio.combine({"a": a, "b": b2}, {"A": ["a"], "B": ["b"]}, "risk")
    assert base[:-1] == moved[:-1]


def test_put_call_parity():
    F, K, v, t = 100.0, 95.0, 0.6, 30 / 365
    c = execution.black_scholes(F, K, v, t, "C")
    p = execution.black_scholes(F, K, v, t, "P")
    assert math.isclose(c - p, F - K, abs_tol=1e-9)


def test_quote_spread_brackets_mid():
    q = execution.QuoteModel()
    bid, ask = q.quote(100.0, 100.0, 0.5, 7 / 365, "C")
    mid = execution.black_scholes(100.0, 100.0, 0.5, 7 / 365, "C")
    assert bid < mid < ask


def test_cost_tiers_monotonic():
    cm = execution.CostModel()
    assert cm.one_side(1e9) < cm.one_side(1e7) < cm.one_side(1e6) < cm.one_side(1e6, spike=True)


def test_cost_split_verdicts():
    assert diagnostics.CostSplit(0.10, 0.0, -0.02).verdict().startswith("positive after")
    assert diagnostics.CostSplit(-0.05, 0.0, -0.02).verdict().startswith("negative even")
    assert diagnostics.CostSplit(0.05, 0.0, -0.10).verdict().startswith("positive before")


def test_stress_behaviour():
    bench = [-0.1, 0.01, 0.02, -0.08, 0.0] * 20
    hedge = [-x for x in bench]
    st = diagnostics.stress_behaviour(hedge, bench, 0.2)
    assert st.mean_return > 0 and st.hit_rate == 1.0


if __name__ == "__main__":                      # run without pytest: python tests/test_riskkit.py
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"{len(tests)} tests passed")
