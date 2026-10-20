"""
Build every figure in docs/figures from the CSV files in results/ (run scripts/parse_results.py first).

    python scripts/make_figures.py
"""
import csv
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
FIG = os.path.join(ROOT, "docs", "figures")
YEARS = [2021, 2022, 2023, 2024, 2025, 2026]

# palette: validated categorical slots + neutral ink (light theme)
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
POS, NEG, MID = "#2a78d6", "#e34948", "#f0efec"
BENCH = "#a8a69e"

for f in ("Inter", "DejaVu Sans"):
    if any(f in x.name for x in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = f
        break
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE, "axes.edgecolor": AXIS,
    "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
    "axes.titlesize": 13, "axes.titleweight": "semibold", "axes.titlelocation": "left", "axes.titlepad": 14,
    "font.size": 10, "legend.frameon": False, "axes.axisbelow": True, "lines.solid_capstyle": "round",
})


def rd(name):
    with open(os.path.join(RES, name), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(v):
    return float(v) if v not in ("", None) else None


def save(fig, name, note=None, y=0.01):
    if note:
        fig.text(0.01, y, note, fontsize=8, color=MUTED, ha="left", va="bottom")
    fig.savefig(os.path.join(FIG, name), dpi=200, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print("wrote", name)


def growth(row):
    g, out = 1.0, [1.0]
    for y in YEARS:
        v = num(row.get(f"y{y}"))
        g *= 1 + (v or 0) / 100
        out.append(g)
    return out


X_GROWTH = [2021] + [y + 1 for y in YEARS[:-1]] + [2026 + 9.6 / 12]       # year-ends; 2026 = to 19 Oct


def fig_portfolio():
    P = {r["name"]: r for r in rd("portfolio.csv")}
    fig, ax = plt.subplots(figsize=(9, 5))
    series = [("Equal risk", BLUE, 2.4, "Portfolio · equal risk"), ("No options (trend + breakout only)", ORANGE, 2.0, "Without options"),
              ("BTC buy & hold (spot)", BENCH, 2.0, "BTC buy & hold")]
    for key, col, lw, lab in series:
        g = growth(P[key])
        ax.plot(X_GROWTH, g, color=col, lw=lw, marker="o", ms=4.5, mec=SURFACE, mew=1.5, label=lab, zorder=3)
        ax.annotate(f"{lab}  {g[-1]:.2f}×", (X_GROWTH[-1], g[-1]), xytext=(8, 0), textcoords="offset points",
                    va="center", fontsize=9.5, color=INK2)
    ax.set_yscale("log")
    ax.set_yticks([0.5, 1, 2, 3])
    ax.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}×"))
    ax.set_xticks(X_GROWTH[:-1] + [X_GROWTH[-1]])
    ax.set_xticklabels(["Jan 21", "Jan 22", "Jan 23", "Jan 24", "Jan 25", "Jan 26", "Oct 26"])
    ax.set_xlim(2020.85, 2027.9)
    ax.axhline(1, color=AXIS, lw=1, zorder=1)
    ax.set_title("Growth of $1 · surviving strategies vs. BTC (year-end values, log scale)")
    ax.legend(loc="upper left", fontsize=9)
    save(fig, "portfolio_growth.png", "Backtest Jan 2021 – Oct 2026. Portfolio = short gamma (daily, weekly), covered call/collar, 14-day strangle, trend; equal risk per family, no leverage.")

    fig, ax = plt.subplots(figsize=(9, 4.2))
    w = 0.38
    xs = range(len(YEARS))
    for k, (key, col, lab) in enumerate((("Equal risk", BLUE, "Portfolio · equal risk"), ("BTC buy & hold (spot)", BENCH, "BTC buy & hold"))):
        vals = [num(P[key][f"y{y}"]) for y in YEARS]
        ax.bar([x + (k - 0.5) * (w + 0.02) for x in xs], vals, width=w, color=col, label=lab, zorder=2)
        if k == 0:
            for x, v in zip(xs, vals):
                ax.annotate(f"{v:+.0f}%", (x - 0.5 * (w + 0.02), v), xytext=(0, 4 if v >= 0 else -12), textcoords="offset points",
                            ha="center", fontsize=8.5, color=INK2)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([str(y) if y < 2026 else "2026 YTD" for y in YEARS])
    ax.axhline(0, color=AXIS, lw=1)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:+.0f}%"))
    ax.set_ylim(-80, 170)
    ax.set_title("Calendar-year returns · portfolio vs. BTC")
    ax.legend(loc="upper right", fontsize=9)
    save(fig, "portfolio_years.png", "2026 runs to 19 Oct and was not used to choose the strategy rules.")


def fig_risk_return():
    S = rd("strategies.csv")
    C = rd("convex.csv")
    P = {r["name"]: r for r in rd("portfolio.csv")}
    pts = []
    for r in S:
        if r["benchmark_of"] or r["name"].startswith(("BTC hold", "Random basket")):
            continue
        grp = "Options" if r["section"] == "hedged" and "grid" not in r["name"].lower() else "Strategies"
        pts.append((r["name"], -num(r["maxdd_pct"]), num(r["cagr_pct"]), grp))
    for r in C:
        tot = num(r["total_pct_at_2pct_risk"]) / 100
        pts.append((r["name"], -num(r["maxdd_pct"]), ((1 + tot) ** (1 / 5.8) - 1) * 100 if tot > -1 else -100, "Options"))
    fig, ax = plt.subplots(figsize=(9.5, 6))
    for grp, col in (("Strategies", ORANGE), ("Options", AQUA)):
        xs = [p[1] for p in pts if p[3] == grp]
        ys = [max(-60, p[2]) for p in pts if p[3] == grp]
        ax.scatter(xs, ys, s=46, color=col, edgecolor=SURFACE, linewidth=1.5, label=grp if grp != "Options" else "Options strategies", zorder=3)
    pe, bt = P["Equal risk"], P["BTC buy & hold (spot)"]
    ax.scatter([-num(pe["maxdd_pct"])], [num(pe["cagr_pct"])], s=130, color=BLUE, edgecolor=SURFACE, linewidth=2, label="Portfolio (equal risk)", zorder=4)
    ax.scatter([-num(bt["maxdd_pct"])], [num(bt["cagr_pct"])], s=90, color=BENCH, edgecolor=SURFACE, linewidth=2, marker="D", label="BTC buy & hold", zorder=4)
    lab = {"Short gamma daily": (8, 4), "Short gamma weekly": (16, -12), "BTC covered call": (6, 9), "Trend 10 (CTA)": (-8, -14),
           "Vol-compression strangle 14D": (8, -13), "30-day breakout v2": (8, -12), "BTC/ETH/SOL rotation": (-10, -14),
           "Low volatility": (-8, 8)}
    for n, x, y, g in pts:
        if n in lab:
            dx, dy = lab[n]
            ax.annotate({"Vol-compression strangle 14D": "Strangle 14D", "Short gamma weekly": "Short gamma weekly (behind portfolio)"}.get(n, n) + (" (SOL hindsight)" if "rotation" in n else ""), (x, max(-60, y)), xytext=(dx, dy), textcoords="offset points",
                        fontsize=8.5, color=INK2, ha="left" if dx > 0 else "right")
    ax.annotate("Portfolio (equal risk)", (-num(pe["maxdd_pct"]), num(pe["cagr_pct"])), xytext=(10, 6), textcoords="offset points", fontsize=9.5, color=INK, weight="semibold")
    ax.annotate("BTC buy & hold", (-num(bt["maxdd_pct"]), num(bt["cagr_pct"])), xytext=(10, 6), textcoords="offset points", fontsize=9, color=INK2, ha="left")
    ax.axhline(0, color=AXIS, lw=1)
    ax.set_xlabel("Maximum drawdown (%)")
    ax.set_ylabel("Annualised return (%)")
    ax.set_xlim(0, 105)
    ax.set_ylim(-65, 100)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"−{v:.0f}%" if v else "0"))
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:+.0f}%"))
    ax.set_title("Return vs. worst drawdown · every backtested strategy")
    ax.legend(loc="upper right", fontsize=9)
    save(fig, "risk_return.png", "Top-left is better. Returns below −60%/yr are drawn at −60%. Options strategies use Black-Scholes prices from DVOL (approximation).")


def fig_costs():
    rows = rd("costs.csv")
    ids = {"altrev": "Alt vs BTC reversion", "breakout30": "30-day breakout", "btc_revert": "BTC reversal", "carry": "Funding carry",
           "ethbtc": "ETH/BTC trend", "fundfade": "Funding fade", "lowvol": "Low volatility", "mburst": "Momentum burst",
           "pumpfade": "Pump fade", "trend10": "Trend 10", "xsrev": "Cross-sectional reversal", "zsnap": "Z-score snapback",
           "breakout2": "30-day breakout v2", "btc_revert2": "BTC reversal v2", "fundfade2": "Funding fade v2", "mburst2": "Momentum burst v2",
           "pumpfade2": "Pump fade v2", "rotation": "Rotation (SOL hindsight)", "trend2": "Trend 10 v2", "volbtc": "BTC vol-managed"}
    data = sorted([(ids.get(r["id"], r["id"]), num(r["price_pct_per_year"]) + num(r["funding_pct_per_year"]), num(r["net_pct_per_year"]))
                   for r in rows if r["id"] != "rotation"], key=lambda z: z[2])
    fig, ax = plt.subplots(figsize=(9.5, 7))
    lo = -100
    for i, (n, pre, net) in enumerate(data):
        for k, (v, col) in enumerate(((pre, BENCH), (net, BLUE if net >= 0 else NEG))):
            y = i + (0.2 if k == 0 else -0.2)
            ax.barh(y, max(lo, v), height=0.36, color=col, zorder=2)
            if v < lo:
                ax.annotate(f"{v:.0f}%", (lo, y), xytext=(4, 0), textcoords="offset points", va="center", fontsize=8, color=SURFACE, weight="semibold")
    ax.set_yticks(range(len(data)))
    ax.set_yticklabels([d[0] for d in data], fontsize=9)
    ax.axvline(0, color=AXIS, lw=1)
    ax.set_xlim(lo, 60)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:+.0f}%"))
    ax.grid(axis="y", visible=False)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=BENCH, label="Before costs (price + funding)"), Patch(color=BLUE, label="After costs · positive"),
                       Patch(color=NEG, label="After costs · negative")], loc="lower right", fontsize=9)
    ax.set_title("Edge before vs. after trading costs (% of capital per year)")
    save(fig, "costs.png", "Simple annual sum of per-trade results. If the grey bar is already negative, the idea has no edge; costs only make it worse.")


def fig_v1_v2():
    S = {(r["version"], r["name"]): r for r in rd("strategies.csv") if r["section"] == "strategies"}
    pairs = [("Trend 10 (CTA)", "Trend 10 v2"), ("BTC reversal", "BTC reversal v2"), ("30-day breakout", "30-day breakout v2"),
             ("Momentum burst", "Momentum burst v2"), ("Funding extremes fade", "Funding extremes fade v2"), ("Pump fade (short)", "Pump fade v2")]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    for i, (a, b) in enumerate(pairs):
        va, vb = num(S[("v1", a)]["cagr_pct"]), num(S[("v2", b)]["cagr_pct"])
        ax.plot([va, vb], [i, i], color=GRID, lw=3, zorder=1, solid_capstyle="round")
        ax.scatter([va], [i], s=70, color=BENCH, edgecolor=SURFACE, linewidth=1.5, zorder=3, label="v1 (original)" if i == 0 else None)
        ax.scatter([vb], [i], s=80, color=BLUE, edgecolor=SURFACE, linewidth=1.5, zorder=4, label="v2 (fewer, stronger trades)" if i == 0 else None)
        ax.annotate(f"{vb:+.0f}%", (vb, i), xytext=(9 if vb >= va else -9, 0), textcoords="offset points", va="center",
                    ha="left" if vb >= va else "right", fontsize=9, color=INK2)
    ax.set_yticks(range(len(pairs)))
    ax.set_yticklabels([p[0].replace(" (CTA)", "").replace(" (short)", "") for p in pairs])
    ax.invert_yaxis()
    ax.axvline(0, color=AXIS, lw=1)
    ax.set_xlim(-75, 30)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:+.0f}%"))
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Annualised return, Jan 2021 – Oct 2026")
    ax.set_title("v1 → v2: rules fixed before seeing results (one variant each)")
    ax.legend(loc="lower right", fontsize=9)
    save(fig, "v1_vs_v2.png", "v2 = liquid coins only, volatility-scaled stops, trailing only in profit, slower signals. Funding fade: v1 and v2 both −19%/yr.", y=-0.05)


def fig_tenor():
    C = {r["name"]: r for r in rd("convex.csv")}
    ks = ["1D", "3D", "7D", "14D"]
    vals = [num(C[f"Vol-compression strangle {k}"]["expectancy_R"]) for k in ks]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(ks, vals, width=0.55, color=[POS if v >= 0 else NEG for v in vals], zorder=2)
    for k, v in zip(ks, vals):
        ax.annotate(f"{v:+.2f}R", (k, v), xytext=(0, 5 if v >= 0 else -14), textcoords="offset points", ha="center", fontsize=10, color=INK)
    ax.axhline(0, color=AXIS, lw=1)
    ax.set_ylim(-0.5, 0.35)
    ax.set_xlabel("Option expiry")
    ax.set_ylabel("Average result per bet (R = premium risked)")
    ax.grid(axis="x", visible=False)
    ax.set_title("Buying strangles when implied vol is cheap: longer expiry wins")
    save(fig, "strangle_tenor.png", "Pre-stated expectation: decay per day falls with expiry. 14D was added after 1D–7D were seen, and confirmed the trend.", y=-0.05)


def fig_corr():
    rows = rd("correlation.csv")
    labels = [r["strategy"] for r in rows]
    cols = list(rows[0].keys())[1:]
    M = [[num(r[c]) for c in cols] for r in rows]
    short = {"Short gamma daily": "Short γ daily", "Short gamma weekly": "Short γ weekly", "BTC covered call": "Covered call", "BTC collar": "Collar",
             "Vol-compression strangle 14D": "Strangle 14D", "Trend 10 (CTA)": "Trend 10", "Trend 10 v2": "Trend 10 v2",
             "30-day breakout v2": "Breakout v2", "Low volatility": "Low vol", "ETH/BTC relative trend": "ETH/BTC",
             "Alt vs BTC reversion": "Alt vs BTC", "BTC spot grid": "BTC grid", "BTC": "BTC"}
    cmap = LinearSegmentedColormap.from_list("div", [NEG, MID, POS])
    fig, ax = plt.subplots(figsize=(10, 7.4))
    im = ax.imshow(M, cmap=cmap, vmin=-1, vmax=1, aspect="auto")
    for i in range(len(M)):
        for j in range(len(M[0])):
            v = M[i][j]
            ax.text(j, i, "1" if i == j else f"{v:.2f}".replace("-0.00", "0.00"), ha="center", va="center", fontsize=8,
                    color=SURFACE if abs(v) > 0.6 and i != j else INK2)
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels([short.get(c, c) for c in cols], rotation=40, ha="right", fontsize=9)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels([short.get(c, c) for c in labels], fontsize=9)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02, ticks=[-1, -0.5, 0, 0.5, 1])
    cb.outline.set_visible(False)
    cb.ax.tick_params(colors=MUTED, labelsize=8)
    ax.set_title("Correlation of daily returns (Jan 2021 – Oct 2026)")
    save(fig, "correlation.png", "Families are mostly independent (|ρ| < 0.2; strongest link trend ↔ 14-day strangle, 0.35). Covered call, collar and the BTC grid are essentially long BTC (ρ 0.8–0.9).", y=-0.06)


def fig_crash():
    rows = rd("crash_days.csv")
    data = sorted([(r["name"], num(r["avg_return_pct_on_worst_10pct_btc_days"])) for r in rows], key=lambda z: z[1])
    fig, ax = plt.subplots(figsize=(9, 5.4))
    for i, (n, v) in enumerate(data):
        col = BENCH if n == "BTC" else (POS if v >= 0 else NEG)
        ax.barh(i, v, height=0.6, color=col, zorder=2)
        ax.annotate(f"{v + 0.0:+.2f}%".replace("-0.00", "0.00"), (v, i), xytext=(5 if v >= 0 else -5, 0), textcoords="offset points", va="center",
                    ha="left" if v >= 0 else "right", fontsize=8.5, color=INK2)
    ax.set_yticks(range(len(data)))
    ax.set_yticklabels([("BTC itself" if n == "BTC" else n) for n, _ in data], fontsize=9)
    ax.axvline(0, color=AXIS, lw=1)
    ax.set_xlim(-6.5, 1.5)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:+.0f}%"))
    ax.grid(axis="y", visible=False)
    ax.set_title("Average return on BTC's worst 10% of days")
    save(fig, "crash_days.png", "Trend and the 14-day strangle gain on crash days; short gamma barely moves; covered call / collar carry the BTC exposure.")


def fig_rotation():
    R = {r["name"]: r for r in rd("rotation.csv")}
    fig, ax = plt.subplots(figsize=(9, 5))
    for key, col, lab in (("Rotation BTC/ETH/SOL (engine)", BENCH, "BTC/ETH/SOL (SOL picked with hindsight)"),
                          ("Rotation BTC/ETH (no SOL)", BLUE, "BTC/ETH"), ("BTC or cash", ORANGE, "BTC or cash")):
        g = growth(R[key])
        ax.plot(X_GROWTH, g, color=col, lw=2.2, marker="o", ms=4.5, mec=SURFACE, mew=1.5, label=lab, zorder=3)
        ax.annotate(f"{g[-1]:.1f}×", (X_GROWTH[-1], g[-1]), xytext=(8, 0), textcoords="offset points", va="center", fontsize=9.5, color=INK2)
    ax.set_yscale("log")
    ax.set_yticks([0.5, 1, 2, 5, 10, 20, 50])
    ax.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}×"))
    ax.set_xticks(X_GROWTH)
    ax.set_xticklabels(["Jan 21", "Jan 22", "Jan 23", "Jan 24", "Jan 25", "Jan 26", "Oct 26"])
    ax.set_xlim(2020.85, 2027.4)
    ax.axhline(1, color=AXIS, lw=1)
    ax.set_title("Dual-momentum rotation: how much was hindsight? (log scale)")
    ax.legend(loc="upper left", fontsize=9)
    save(fig, "rotation.png", "Weekly: hold the best 28-day performer if positive, else cash. Removing SOL cuts the result from 44× to 4.3×.")


def fig_selection():
    rows = rd("selection.csv")
    order = ["Top 4 by Sharpe", "All with Sharpe ≥ 0.5 (10)", "Top 4 by return", "4 most independent (Sharpe ≥ 0.5)", "BTC buy & hold"]
    R = {r["method"]: r for r in rows}
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    for i, k in enumerate(order):
        r = R[k]
        a, b = num(r["sharpe_2021_23"]), num(r["sharpe_2024_26"])
        bench = k.startswith("BTC")
        ax.plot([a, b], [i, i], color=GRID, lw=3, zorder=1, solid_capstyle="round")
        ax.scatter([a], [i], s=70, color=BENCH, edgecolor=SURFACE, linewidth=1.5, zorder=3, label="2021–2023 (used to choose)" if i == 0 else None)
        ax.scatter([b], [i], s=85, color=BENCH if bench else BLUE, edgecolor=SURFACE, linewidth=1.5, zorder=4,
                   label="2024–2026 (never seen)" if i == 0 else None)
        ax.annotate(f"{b:.2f}   ·   {num(r['cagr_2024_26_pct']):+.0f}%/yr, max DD {num(r['maxdd_2024_26_pct']):.0f}%", (b, i),
                    xytext=(-10, 0) if b < a else (10, 0), textcoords="offset points", va="center",
                    ha="right" if b < a else "left", fontsize=8.5, color=INK2)
        ax.annotate(f"{a:.2f}", (a, i), xytext=(9, 0) if b < a else (-9, 0), textcoords="offset points", va="center",
                    ha="left" if b < a else "right", fontsize=8.5, color=MUTED)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(order, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlim(-1.6, 4.4)
    ax.axvline(0, color=AXIS, lw=1)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Sharpe ratio of an equal-risk portfolio of the chosen strategies")
    ax.set_title("Choose with 2021–2023, then measure on 2024–2026")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, fontsize=9)
    save(fig, "selection.png", "Every method decays out of sample. Choosing for stability (Sharpe) keeps the best risk-adjusted result; choosing for low correlation alone keeps the least.", y=-0.15)


def main():
    os.makedirs(FIG, exist_ok=True)
    fig_portfolio()
    fig_risk_return()
    fig_costs()
    fig_v1_v2()
    fig_tenor()
    fig_corr()
    fig_crash()
    fig_rotation()
    fig_selection()


if __name__ == "__main__":
    main()
