"""
Turn the raw text output of backtest.py / analyze.py (results/*.txt, Greek labels) into tidy English CSV files
(results/*.csv) that the figures and the README tables are built from.

    python scripts/parse_results.py
"""
import csv
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
YEARS = [2021, 2022, 2023, 2024, 2025, 2026]

NAME = {
    # strategies (names already English in the engine)
    "BTC reversal": "BTC reversal", "Funding carry": "Funding carry", "Trend 10 coins (CTA)": "Trend 10 (CTA)",
    "ETH/BTC relative trend": "ETH/BTC relative trend", "Z-score snapback": "Z-score snapback",
    "Alt vs BTC reversion": "Alt vs BTC reversion", "Low volatility": "Low volatility",
    "Cross-sectional reversal (1D)": "Cross-sectional reversal (1D)", "Momentum burst": "Momentum burst",
    "Funding extremes fade": "Funding extremes fade", "30-day breakout": "30-day breakout", "Pump Fade (short)": "Pump fade (short)",
    "BTC hold": "BTC hold (1x perp, pays funding)", "Random basket (placebo)": "Random basket (placebo)",
    "Trend 10 v2": "Trend 10 v2", "BTC volatility-managed": "BTC volatility-managed", "BTC/ETH/SOL rotation": "BTC/ETH/SOL rotation",
    "BTC reversal v2": "BTC reversal v2", "30-day breakout v2": "30-day breakout v2", "Momentum burst v2": "Momentum burst v2",
    "Funding extremes fade v2": "Funding extremes fade v2", "Pump Fade v2": "Pump fade v2",
    # grid
    "BTC grid · χαμηλή volatility": "BTC spot grid", "SOL grid neutral · μεσαία volatilit": "SOL grid (hedged)",
    "kPEPE grid neutral · μεγάλη volatil": "kPEPE grid (hedged)", "SOL grid neutral v2 · μόνο σε ήρεμη": "SOL grid (hedged) v2 · calm only",
    "kPEPE grid neutral v2 · μόνο σε ήρε": "kPEPE grid (hedged) v2 · calm only",
    "κράτημα BTC": "hold BTC", "κράτημα SOL": "hold SOL", "κράτημα kPEPE": "hold kPEPE",
    # hedged
    "Protected Grid BTC": "Protected grid BTC", "Protected Grid BTC v2": "Protected grid BTC v2",
    "σύγκριση (ίδιο χωρίς προστασία)": "same grid, no put", "σύγκριση (κράτημα)": "hold BTC",
    "Long Gamma Weekly": "Long gamma weekly", "Short Gamma Weekly": "Short gamma weekly", "Long Gamma Daily": "Long gamma daily",
    "Short Gamma Daily": "Short gamma daily", "BTC Covered Call": "BTC covered call", "BTC Collar": "BTC collar",
    "Vol Spread BTC / ETH": "Vol spread BTC/ETH",
    # convex
    "Vol Compression Strangle 1D": "Vol-compression strangle 1D", "Vol Compression Strangle 3D": "Vol-compression strangle 3D",
    "Vol Compression Strangle 7D": "Vol-compression strangle 7D", "Vol Compression Strangle 14D": "Vol-compression strangle 14D",
    "Delta-Hedged Long Gamma": "Delta-hedged long gamma", "Liquidation Wick Reversion": "Liquidation wick reversion",
    "Volatility Compression Breakout": "Volatility-compression breakout",
    # portfolio / rotation
    "Ίσο κεφάλαιο · ΧΩΡΙΣ breakout": "Equal capital", "Ίσο ρίσκο · ΧΩΡΙΣ breakout": "Equal risk",
    "Ίσο κεφάλαιο · ΜΕ breakout": "Equal capital + breakout", "Ίσο ρίσκο · ΜΕ breakout": "Equal risk + breakout",
    "Χωρίς options (μόνο Trend + Breakou": "No options (trend + breakout only)", "BTC (απλό κράτημα)": "BTC buy & hold (spot)",
    "Rotation του backtest (κινητήρας)": "Rotation BTC/ETH/SOL (engine)", "BTC/ETH/SOL (ξαναϋπολογισμός)": "Rotation BTC/ETH/SOL (recomputed)",
    "BTC/ETH (χωρίς SOL)": "Rotation BTC/ETH (no SOL)", "μόνο BTC (BTC ή μετρητά)": "BTC or cash",
    "sgd": "Short gamma daily", "sgw": "Short gamma weekly", "cc": "BTC covered call", "collar": "BTC collar",
    "vcs14": "Vol-compression strangle 14D", "trend10": "Trend 10 (CTA)", "breakout2": "30-day breakout v2",
}
PCT = r"([+-]?\d+(?:\.\d+)?)%"
ROW = re.compile(r"^(?P<name>.+?)\s+" + PCT + r"\s+" + PCT + r"\s+" + PCT + r"\s+(-?\d+\.\d+)\s+(?P<rest>.*)$")


def years(rest):
    toks = re.findall(r"[+-]?\d+(?:\.\d+)?%|–", rest)[:6]
    return [None if t == "–" else float(t[:-1]) for t in toks] + [None] * (6 - len(toks))


def read(name):
    with open(os.path.join(RES, name), encoding="utf-8") as f:
        return f.read().splitlines()


def write(name, head, rows):
    with open(os.path.join(RES, name), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(head)
        w.writerows(rows)
    print("wrote", name, len(rows), "rows")


def table_rows(lines, section, version, extra_parent=True):
    out, parent = [], None
    for ln in lines:
        m = ROW.match(ln)
        if not m:
            continue
        raw = m.group("name").strip()
        sub = ln.startswith("   ")
        if raw == "v1":
            continue
        name = NAME.get(raw, raw)
        tr = re.search(r"(\d+)\s+(κλεισ\.|stop|κύκλοι)", ln)
        since = re.search(r"από (\d\d)/(\d{4})", ln)
        out.append(dict(section=section, version=version, name=name, benchmark_of=(parent if sub else ""),
                        total=float(m.group(2)), cagr=float(m.group(3)), maxdd=float(m.group(4)), sharpe=float(m.group(5)),
                        years=years(m.group("rest")), trades=int(tr.group(1)) if tr else "", since=f"{since.group(2)}-{since.group(1)}" if since else ""))
        if not sub:
            parent = name
    return out


def split(lines, start, stops):
    i = next(k for k, l in enumerate(lines) if l.startswith(start))
    j = next((k for k in range(i + 1, len(lines)) if any(lines[k].startswith(s) for s in stops)), len(lines))
    return lines[i:j]


def main():
    v2, an = read("backtest_run.txt"), read("analysis.txt")
    v1 = v2                                             # one full run holds both the v1 and the v2 tables
    rows = []
    rows += table_rows(split(v1, "STRATEGIES (", ["GRID", "CONVEX", "HEDGED"]), "strategies", "v1")
    v2s = split(v2, "STRATEGIES v2", ["Μόνο live", "GRID"])
    rows += [r for r in table_rows(v2s, "strategies", "v2") if r["name"] not in ("BTC hold (1x perp, pays funding)", "Random basket (placebo)")]
    rows += [dict(r, version="v2" if "v2" in r["name"] else "v1") for r in table_rows(split(v2, "GRID BOTS", ["CONVEX"]), "grid", "")]
    rows += [dict(r, version="v2" if "v2" in r["name"] else "v1") for r in table_rows(split(v2, "HEDGED", ["Στήλες"]), "hedged", "")]
    write("strategies.csv", ["section", "version", "name", "benchmark_of", "total_pct", "cagr_pct", "maxdd_pct", "sharpe"] + [f"y{y}" for y in YEARS] + ["trades", "since"],
          [[r["section"], r["version"], r["name"], r["benchmark_of"], r["total"], r["cagr"], r["maxdd"], r["sharpe"]] + r["years"] + [r["trades"], r["since"]] for r in rows])
    # convex
    cv = []
    for ln in split(v2, "CONVEX", ["HEDGED"]):
        m = re.match(r"^(.+?)\s+(\d+)\s+(\d+)%\s+([\d.]+)R\s+([+-][\d.]+)R\s+" + PCT + r"\s+" + PCT + r"\s+(\d+)\s+(.*)$", ln)
        if m:
            cv.append([NAME.get(m.group(1).strip(), m.group(1).strip()), int(m.group(2)), float(m.group(3)), float(m.group(4)), float(m.group(5)),
                       float(m.group(6)), float(m.group(7)), int(m.group(8))] + years(m.group(9)))
    write("convex.csv", ["name", "bets", "hit_pct", "avg_win_R", "expectancy_R", "total_pct_at_2pct_risk", "maxdd_pct", "worst_losing_streak"] + [f"y{y}" for y in YEARS], cv)
    # costs
    co, ver = [], None
    for ln in an:
        if ln.startswith("--- "):
            ver = ln[4:].strip()
        m = re.match(r"^([a-z0-9_]+)\s+(\d+)\s+" + PCT + r"\s+" + PCT + r"\s+" + PCT + r"\s+" + PCT, ln)
        if m and ver:
            co.append([ver, m.group(1), int(m.group(2))] + [float(m.group(k)) for k in range(3, 7)])
    write("costs.csv", ["version", "id", "trades", "price_pct_per_year", "funding_pct_per_year", "costs_pct_per_year", "net_pct_per_year"], co)
    # correlation
    sec = split(an, "2. CORRELATION", ["Στις κακές"])
    labels = ["Short gamma daily", "Short gamma weekly", "BTC covered call", "BTC collar", "Vol-compression strangle 14D", "Trend 10 (CTA)",
              "Trend 10 v2", "30-day breakout v2", "Low volatility", "ETH/BTC relative trend", "Alt vs BTC reversion", "BTC spot grid", "BTC"]
    mat = []
    for ln in sec:
        vals = re.findall(r"(-?\d+\.\d+|·)", ln[20:])
        if len(vals) == 13 and not ln.startswith(" "):
            mat.append([1.0 if v == "·" else float(v) for v in vals])
    write("correlation.csv", ["strategy"] + labels, [[labels[i]] + row for i, row in enumerate(mat)])
    cr = []
    for ln in split(an, "Στις κακές", ["====="]):
        m = re.match(r"^\s+(.+?)\s+([+-]\d+\.\d+)% τη μέρα(?:\s+corr\s+(-?\d+\.\d+))?", ln)
        if m:
            nm = m.group(1).strip()
            nm = {"Short Gamma Daily": "Short gamma daily", "Short Gamma Weekly": "Short gamma weekly", "Covered Call": "BTC covered call",
                  "Collar": "BTC collar", "Strangle 14D": "Vol-compression strangle 14D", "Trend 10": "Trend 10 (CTA)", "Breakout v2": "30-day breakout v2",
                  "ETH/BTC": "ETH/BTC relative trend", "Alt vs BTC": "Alt vs BTC reversion", "BTC grid": "BTC spot grid"}.get(nm, nm)
            cr.append([nm, float(m.group(2)), float(m.group(3)) if m.group(3) else ""])
    write("crash_days.csv", ["name", "avg_return_pct_on_worst_10pct_btc_days", "corr_on_those_days"], cr)
    pf = table_rows(split(an, "3. ΧΑΡΤΟΦΥΛΑΚΙΟ", ["====="]) + split(an, "Ίσο κεφάλαιο · ΧΩΡΙΣ", ["Το «χωρίς"]), "portfolio", "")
    seen, prow = set(), []
    for r in pf:
        if r["name"] in seen:
            continue
        seen.add(r["name"])
        prow.append([r["name"], r["total"], r["cagr"], r["maxdd"], r["sharpe"]] + r["years"])
    write("portfolio.csv", ["name", "total_pct", "cagr_pct", "maxdd_pct", "sharpe"] + [f"y{y}" for y in YEARS], prow)
    ro = table_rows(split(an, "4. ROTATION", ["Οι δύο"]), "rotation", "")
    write("rotation.csv", ["name", "total_pct", "cagr_pct", "maxdd_pct", "sharpe"] + [f"y{y}" for y in YEARS],
          [[r["name"], r["total"], r["cagr"], r["maxdd"], r["sharpe"]] + r["years"] for r in ro])
    # selection test: choose with 2021-2023 only, measure on 2024-2026
    METHOD = {"Οι 4 πιο κερδοφόρες (CAGR)": "Top 4 by return", "Οι 4 με το καλύτερο Sharpe": "Top 4 by Sharpe",
              "Οι 4 πιο ανεξάρτητες (Sharpe ≥ 0.5)": "4 most independent (Sharpe ≥ 0.5)",
              "Όλες με Sharpe ≥ 0.5 (10)": "All with Sharpe ≥ 0.5 (10)", "BTC (απλό κράτημα)": "BTC buy & hold"}
    STRAT = {"Rotation B/E/S": "BTC/ETH/SOL rotation", "Short gamma D": "Short gamma daily", "Short gamma W": "Short gamma weekly",
             "30d breakout v2": "30-day breakout v2", "ETH/BTC trend": "ETH/BTC relative trend", "Covered call": "BTC covered call"}
    sel, cur = [], None
    for ln in split(an, "5. ΕΠΙΛΟΓΗ", ["Πώς διαβάζεται"]):
        m = re.match(r"^(.+?)\s+" + r"\s+".join([PCT, PCT, r"(-?\d+\.\d+)"] * 2) + r"\s+" + r"\s+".join([PCT] * 3) + r"\s*$", ln)
        if m:
            cur = [METHOD.get(m.group(1).strip(), m.group(1).strip())] + [float(m.group(k)) for k in range(2, 11)] + ["", ""]
            sel.append(cur)
        elif cur and ln.strip().startswith("→"):
            cur[10] = "; ".join(STRAT.get(x.strip(), x.strip()) for x in ln.strip()[1:].split(","))
        elif cur and "correlation" in ln:
            cur[11] = float(re.findall(r"(\d+\.\d+)\s*$", ln)[0])
    write("selection.csv", ["method", "cagr_2021_23_pct", "maxdd_2021_23_pct", "sharpe_2021_23", "cagr_2024_26_pct", "maxdd_2024_26_pct",
                            "sharpe_2024_26", "y2024", "y2025", "y2026", "chosen", "avg_abs_corr_2021_23"], sel)


if __name__ == "__main__":
    main()
