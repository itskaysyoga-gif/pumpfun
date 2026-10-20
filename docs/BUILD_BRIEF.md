# pumplab — Build Brief (v2, 2026-10-20)

## Purpose and honest premise
Find out, with real data and before risking money, whether any pump.fun trading
rule makes money after all costs. Live trading with the $100 happens only if every
go/no-go criterion passes.

Expectation: most rules will test negative. Professional snipers have private
infrastructure, fees are dynamic and taken on both legs, and most launches dump on
early buyers. Honest odds that a rule passes the gate for a $100 retail setup:
low (roughly 1 in 5 or worse). Nothing in this plan guarantees profit. What it
guarantees is that the answer is measured, cheap, and costs at most $100 + ~$10/month.

## Non-negotiable rules
See `CLAUDE.md`. Summary: no third-party bot code; pinned minimal deps; no keys
before Phase 7; isolated VM; paper mode by default; verify every on-chain value;
no manipulation.

## Budget
| Item | Choice | Cost |
| --- | --- | --- |
| Development | Claude Code on the existing Max plan | $0 extra |
| Server | Hetzner/DO VM, 2 vCPU / 4 GB / 40 GB | ~$5–10/month |
| Data | Solana `logsSubscribe` via public RPC, Helius free tier as fallback | $0 |
| Storage | JSONL → Parquet + DuckDB on the VM | $0 |
| Alerts | Telegram bot | $0 |
| Live capital | Burner wallet, SOL only | $100 max, Phase 7 only |

Rejected: PumpPortal metered trade stream (0.01 SOL per 10k events; at pump.fun
volume that is likely dollars to hundreds of dollars per day). Paid RPC/gRPC
($49–499+/month): a strategy that only works with it fails the gate. Vercel: can't
hold a 24/7 websocket; not needed.

## Architecture
collect → label → simulate → paper-trade → execute, one Python codebase, one data
store. Simulator and live executor share strategy code.

- **Collector** (built): `logsSubscribe` on the pump program, decodes Create /
  Trade / Complete events from the official IDL (`docs/idl/pump.json`), hourly
  JSONL, gap log, silence watchdog, Telegram alerts. Parquet rollup hourly.
- **Labeler**: per SOL-quoted token: price path at 10s/30s/1m/5m/15m/30m/60m,
  peak multiple, time to peak, graduated?, max drawdown, creator's prior launches,
  early-holder concentration, unique buyers, holder-rewards flag.
- **Wallet scorer**: per wallet, realised PnL on pump.fun round trips, win rate,
  holding time. Used by strategy 6.
- **Simulator**: replays events with entry delayed by realistic latency (default
  2 slots; tested 1–5), price impact computed from the bonding-curve reserves in
  the events, fees taken from the observed fee bps at that market cap, priority
  fee + tip per transaction, both legs.
- **Risk manager**: sits between strategy and order; enforces all limits below;
  kill state persists until a human clears it.

## Phases
| Phase | What | Done when |
| --- | --- | --- |
| 0 Setup | Repo, deps, assumptions, collector code, tests | **Done** (see phase-0 report) |
| 1 Collect | VM, probe, run collector 14+ days | Probe OK; 72h with <1% gap time; 20 tokens spot-checked vs explorer |
| 2 Label + explore | Labeler, exploration report | Report shows what a token's first hour looks like, with numbers |
| 3 Simulator | Fill model + tests + calibration | Do-nothing = 0 PnL; hand-calculated fee case matches |
| 4 Research | Six strategies on time-split data | Results table on untouched last 20% |
| 5 Paper | Best 1–2 live with simulated fills, 7 days | Paper vs backtest compared |
| 6 Go/no-go | Apply gate | Owner decides |
| 7 Live micro | Burner wallet, $100 max, half size 3 days | Budget stop hit or 4 weeks |
| 8 Post-mortem | Live vs paper vs backtest | Decision recorded |

### Phase 4 strategies (fixed list; no endless tuning)
1. **Launch snipe** baseline: buy every new token at T+latency, fixed TP / time exit. Expected to lose.
2. **Momentum filter**: buy after X buys and Y unique buyers in first minute; trailing stop.
3. **Graduation play**: buy at 80–95% curve progress; sell around migration.
4. **Post-graduation pullback**: graduated tokens after 40–60% drawdown with volume; tight stop.
5. **Creator / holder filter** overlay on 2–4: skip serial ruggers and concentrated early holders.
6. **Wallet following**: wallets that were consistently profitable in the design split
   (not just lucky: min 30 round trips, positive median trade); follow their buys at
   T+latency in later splits. Public on-chain data only.

Testing rules: split by time 60% design / 20% tune / 20% untouched. Report for each:
trades, win rate, avg win/loss, net PnL after all costs, max drawdown, PnL with
latency doubled, PnL excluding the single best trade.

## Go/no-go gate (all must pass)
| # | Criterion | Threshold |
| --- | --- | --- |
| 1 | Net PnL after costs, untouched test split | Positive |
| 2 | Same, latency doubled | Positive |
| 3 | Same, excluding single best trade | Positive |
| 4 | Test-split trades | ≥ 100 |
| 5 | 7-day paper vs backtest | Same sign, within 50% |
| 6 | Max drawdown, test + paper | < 40% of capital |

## Live risk limits (enforced in code)
- $5 per trade ($2.50 first 3 days); max 2 open positions.
- Daily loss stop $10; total stop when balance ≤ $50 → kill switch until human reset.
- Priority fee + tip capped per transaction; skip if exceeded.
- No trading if the data stream lagged > 3 s in the last minute.
- `scripts/flatten.py` sells everything independently of strategy code.

## Timeline
Week 1: VM + probe + collector running. Weeks 2–3: labeler, simulator, exploration
(collector keeps running). Week 3–4: strategy research. Week 4–5: paper trading.
~Week 5: go/no-go. Weeks 6–9: live micro-trading if go. This fits a 2–3 month horizon.
