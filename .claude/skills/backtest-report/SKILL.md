---
name: backtest-report
description: Rules and report format for evaluating a pumplab trading strategy honestly (time splits, full costs, robustness checks, go/no-go table). Use whenever running, comparing or reporting strategy backtests or paper-trading results (Phases 4-6).
effort: high
---

# Honest strategy evaluation

## Data rules
- SOL-quoted coins only (`quote_mint` is wrapped SOL or null on old events).
- Exclude any period inside a gap from `data/gaps.jsonl`, plus 5 minutes after it.
- Time split over the full collected range: first 60% = design, next 20% = tune,
  last 20% = test. The test split is run ONCE per strategy, at the end. Record the split
  timestamps in the report. Never change parameters after seeing test results.

## Cost rules (every simulated trade, both legs)
- Entry fill at the first trade at or after signal slot + latency (default 2 slots).
- Price impact from bonding-curve reserves in the events, for our size.
- Protocol + creator fee bps as observed in TradeEvents at that market cap.
- Priority fee + tip: config value per transaction (default 0.0005 SOL), both legs.
- A sell that cannot fill (curve migrated/frozen, no liquidity) is marked at the last price
  available after migration, or zero if none within 1 hour.

## Required numbers per strategy
| Metric | Design | Tune | Test |
| --- | --- | --- | --- |
| Trades | | | |
| Win rate | | | |
| Avg win / avg loss (SOL) | | | |
| Net PnL after all costs (SOL and % of $100 capital) | | | |
| Max drawdown | | | |
| Net PnL, latency x2 | | | |
| Net PnL, excluding single best trade | | | |
| Fees + tips as % of gross PnL | | | |

## Verdict
Apply the go/no-go gate from `docs/BUILD_BRIEF.md` criterion by criterion, as a table with
pass/fail. One fail = no-go. State the verdict in the first line of the report.
Have the `reviewer` subagent check the numbers and code before reporting to the owner.
