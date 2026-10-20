# Strategy catalogue

Every strategy that was tested, described at the level of its idea, with its backtest result (January 2021 – October 2026).
The production code and its parameters are not part of this repository. Exact thresholds, position sizes and filters are left out on purpose.

- **CAGR** = annualised return. **Max DD** = worst peak-to-trough fall. **Sharpe** = annualised return per unit of volatility.
- Strategies that *buy* option premium are measured per bet, in **R** (1R = the premium at risk).
- Option prices are reconstructed from Deribit's DVOL index (see [methodology](methodology.md#6-options-an-approximation)).

## Directional and factor strategies · original rules (v1)

| Strategy | Idea | CAGR | Max DD | Sharpe | Reading |
|---|---|---:|---:|---:|---|
| Trend 10 (CTA) | Time-series trend on ten large coins, each sized to equal risk | +9% | −17% | 0.76 | Positive in 5 of 6 years; gains on crash days |
| Low volatility | Long calm coins, short volatile ones, equal risk per coin | +23% | −46% | 0.71 | Profitable, but not market-neutral (ρ 0.47 to BTC) |
| ETH/BTC relative trend | Trend of the ETH/BTC ratio, market-neutral | +3% | −24% | 0.28 | Small |
| Funding carry | Long the cheapest-funding coins, short the most expensive | +1% | −58% | 0.17 | Funding earned is lost on price and costs |
| BTC reversal | Fade unusually large daily BTC moves | −6% | −36% | −0.43 | No premium |
| Funding extremes fade | Fade crowded positioning signalled by extreme funding | −19% | −81% | −0.44 | Collects funding, loses it to costs |
| Alt vs BTC reversion | Beta-hedged mean reversion of alts against BTC | −23% | −84% | −0.78 | No premium |
| 30-day breakout | Buy new 30-day highs on rising volume | −26% | −93% | −0.29 | Small premium, consumed by costs |
| Pump fade | Short coins after an extreme one-day pump | −29% | −88% | −1.15 | Momentum continues more often than not |
| Cross-sectional reversal | Long yesterday's losers, short yesterday's winners | −59% | −100% | −2.43 | Negative before costs; costs multiply it |
| Momentum burst | Follow unusually large hourly moves on high volume | −64% | −100% | −2.83 | Negative before costs |
| Z-score snapback | Fade short-term stretches from the intraday mean | −90% | −100% | −4.32 | Negative before costs; ~16,000 trades |

## Same ideas, revised execution (v2)

The revisions were decided before testing, one per strategy. They share one theme: fewer and stronger signals, liquid coins only, exits scaled to each coin's volatility, trailing stops only once a position is in profit.

| Strategy | What changed | CAGR | Max DD | Sharpe | vs. v1 |
|---|---|---:|---:|---:|---|
| 30-day breakout v2 | Largest coins only, plus a market-regime filter | +15% | −71% | 0.49 | −26% → +15%, but driven by 2021 and 2023 |
| Trend 10 v2 | Slower signals, less frequent rebalancing | +8% | −17% | 0.69 | Same result with a third of the trades |
| BTC reversal v2 | Extreme moves only, symmetric exits | +1% | −27% | 0.15 | −6% → +1% |
| Pump fade v2 | Waits for the pump to break before shorting | −9% | −46% | −0.76 | Less negative |
| Momentum burst v2 | Fewer, larger signals; trailing exit | −18% | −81% | −0.67 | Less negative |
| Funding extremes fade v2 | Liquid coins, volatility-scaled exits | −19% | −85% | −0.11 | No change |
| BTC volatility-managed *(new)* | Constant-risk BTC exposure | +10% | −68% | 0.42 | Smaller drawdown than holding, lower Sharpe |
| BTC/ETH/SOL rotation *(new)* | Weekly dual momentum across three coins | +95% | −70% | 1.22 | Selection bias: +28%/yr without SOL ([details](../README.md#6-selection-bias-a-44-return-that-was-mostly-hindsight)) |

## Options · buying volatility when it is cheap

| Strategy | Idea | Average per bet (R) | Max DD at 2% risk per bet | Hit rate | Reading |
|---|---|---:|---:|---:|---|
| Strangle 14D | Buy out-of-the-money strangles when implied vol is historically cheap | **+0.21R** | −29% | 37% | Positive in 5 of 6 years; gains on crash days |
| Strangle 7D | Same, 7-day expiry | +0.06R | −49% | 32% | Break-even |
| Strangle 3D | Same, 3-day expiry | −0.14R | −87% | 25% | Pays the volatility premium |
| Strangle 1D | Same, 1-day expiry | −0.39R | −100% | 18% | Pays the volatility premium |
| Delta-hedged long gamma | Long straddle, hedged continuously | −0.24R | −66% | 10% | Pays the volatility premium |
| Volatility-compression breakout | Trade the break of an unusually tight range | −0.05R | −100% | 32% | No premium; many trades |
| Wick reversion | Provide liquidity at extreme one-minute wicks | −0.10R | −99% | 47% | Exchange-specific; not testable on another venue's data |

## Options · hedged and always on

| Strategy | Idea | CAGR | Max DD | Sharpe | Reading |
|---|---|---:|---:|---:|---|
| Short gamma, daily | Sell at-the-money straddles with protective wings, delta-hedged | +41% | −12% | 3.72 | Strongest result; depends most on the options model |
| Short gamma, weekly | Same, weekly expiry | +19% | −7% | 3.42 | Steady in every year |
| Long gamma, daily / weekly | The exact mirror (control group) | −76% / −34% | −100% / −91% | −14.16 / −9.10 | Confirms the premium |
| BTC covered call | Hold BTC, sell an out-of-the-money call every week | +23% | −53% | 0.69 | Beats holding (+19%, −77%) |
| BTC collar | Hold BTC, sell a call, buy a put | +16% | −49% | 0.56 | Lower return, much lower drawdown |
| Protected grid (v1 / v2) | Spot grid plus a monthly protective put (v2: only when vol is cheap) | −7% / −1% | −84% / −71% | 0.02 / 0.08 | The put costs more than it saves (same grid without the put: 0%, −68%) |
| Vol spread BTC/ETH | Sell the relatively expensive volatility, buy the cheap one | −6% | −32% | −3.80 | No premium |

## Grids

| Strategy | Idea | CAGR | Max DD | Reading |
|---|---|---:|---:|---|
| BTC spot grid | Buy dips, sell rallies inside a band | +13% | −51% | Behaves like holding about half the BTC (hold: +19%, −77%) |
| SOL / kPEPE hedged grids | Same, with a short hedge to stay market-neutral | −16% / −21% | −80% / −72% | Trends overwhelm the grid income |
| Hedged grids, calm markets only (v2) | Paused in high-volatility regimes | −14% / −11% | −64% / −44% | Less negative, still negative |

## Measured forward only

Some strategies depend on data that has no free history: open interest, liquidation flows, large-trader positioning, the option volatility smile, and a macro event calendar. They run in paper trading only, so their results are not included here.
