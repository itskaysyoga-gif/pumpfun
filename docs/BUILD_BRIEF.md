# pumplab — Build Brief (v3, 2026-10-20)

## 1. Purpose and honest premise
Find out, with real on-chain data and before risking money, whether any pump.fun trading
rule makes money after all costs. Live trading with the $100 happens only if every
go/no-go criterion passes.

Expectation: most rules will test negative. Professional snipers have private
infrastructure; fees are dynamic and charged on both legs; most launches dump on early
buyers. Honest odds that a rule passes the gate for a $100 retail setup: roughly 1 in 5
or worse. Nothing here guarantees profit. What it guarantees: a measured answer in about
5 weeks, for at most ~$29/month plus the $100, which stays untouched until Phase 7.

## 2. Decisions (final unless data proves them wrong)
| Topic | Decision | Why |
| --- | --- | --- |
| Where code runs | DigitalOcean droplet, FRA1, 2 vCPU / 4 GB / 80 GB, Ubuntu 24.04 | 24/7 collector; reaches Solana RPC; data and analysis in one place |
| Where you work | claude.ai/code or Claude phone app, connected by **Remote Control** to Claude Code running on the droplet (in tmux) | Same browser experience as claude.ai/code, but Claude sits next to the data and the live stream |
| Not used | claude.ai/code cloud sessions for running code; Vercel; Hetzner | Cloud sessions are temporary VMs with restricted network and no persistent data; Vercel can't hold a websocket |
| Claude account | Your Max plan, logged in on the droplet | No API costs |
| Data source | Solana `logsSubscribe` on the pump program; public RPC first, free Helius key as fallback | Free; PumpPortal trade stream is metered and too expensive |
| Fees in research | Actual fee bps per trade from TradeEvents | Fees are dynamic tiers since Sept 2025 |
| Coins in scope | SOL-quoted pump coins only | USDC / pump-coin-quoted pairs are new and different |
| Language / deps | Python 3.12+, uv, pinned minimal deps | Auditable, no third-party bot code |
| Live wallet (Phase 7) | New burner keypair owned by a separate Linux user `trader`; Claude Code's user `pumplab` cannot read it; $100 max | Key never reachable by the coding agent |

## 3. Models
| Work | Model | Effort | How |
| --- | --- | --- | --- |
| Default for all phases | **Opus 5.5** (`opus`) | medium (default) | Set in `.claude/settings.json` |
| Simulator, risk manager, strategy research, go/no-go | Opus 5.5 | **high** (skills `phase-run`, `backtest-report` set this) | Automatic via skill |
| Independent review of money-related code and results | Opus 5.5 | default | `reviewer` subagent |
| Collector health checks | **Sonnet 5.5** (`sonnet`) | low | `health` skill sets this; saves usage |
| Not used | Haiku, Fable, opusplan | | Haiku too weak for quant work; Fable not needed and heavier on limits; opusplan adds switching with little gain |

If you hit Max usage limits mid-phase, switch with `/model sonnet` for routine coding and go
back to `/model opus` for simulator and research work.

## 4. Claude Code skills and agents (in the repo, load automatically on the droplet)
| Name | Type | Use |
| --- | --- | --- |
| `/phase-run N` | skill | Runs exactly one phase: orient, build, test, review, report, push, 8-line summary |
| `/health` | skill (Sonnet) | Collector status, gap %, disk; fixes common problems |
| `/backtest-report` | skill | Honest evaluation rules and the report table for Phases 4–6 |
| `reviewer` | subagent (Opus) | Skeptical review: look-ahead bias, missing costs, overfitting, safety rules |

More skills get added when a procedure repeats (e.g. `/paper-status` in Phase 5,
`/flatten` in Phase 7).

## 5. Architecture
collect → label → simulate → paper-trade → execute. One Python codebase, one data store;
the simulator and the live executor call the same strategy code.

- **Collector** (built): `logsSubscribe`, decodes Create/Trade/Complete events from the
  official IDL, hourly JSONL, gap log, 60 s silence watchdog, Telegram alerts. systemd
  user service. Hourly rollup to Parquet; raw kept gzipped.
- **Labeler**: per token: price path at 10s/30s/1m/5m/15m/30m/60m, peak multiple, time to
  peak, graduated?, max drawdown, creator's prior launches, early-holder concentration,
  unique buyers, holder-rewards flag.
- **Wallet scorer**: per wallet realised PnL, win rate, holding time (strategy 6).
- **Simulator**: entry at signal slot + latency (default 2, tested 1–5); price impact from
  curve reserves; observed fee bps; priority fee + tip; both legs.
- **Risk manager**: between strategy and order; enforces section 8; kill state persists.

## 6. Phases
| Phase | What | Done when | Owner does |
| --- | --- | --- | --- |
| 0 Setup | Repo, decoder, collector, skills, droplet guide | **Done** | — |
| 1 Collect | Probe, start collector, rollup timer, 72 h check, explorer spot-check | Probe OK; 72 h with <1% gap; 20 tokens match explorer | DigitalOcean guide; then `/phase-run 1` |
| 2 Label + explore | Labeler, wallet scorer, exploration report | First-hour profile of a typical token, in numbers | Read report |
| 3 Simulator | Fill model, tests, calibration vs real fills | Do-nothing = 0; fee case matches hand calc; reviewer PASS | — |
| 4 Research | Six strategies, time-split (needs ≥14 days data) | Results table on untouched test split; reviewer PASS | Read report |
| 5 Paper | Best 1–2 strategies live, simulated fills, 7 days | Paper vs backtest compared | — |
| 6 Go/no-go | Apply gate | Owner decides | **Decide** |
| 7 Live micro | `trader` user, burner wallet, $100 max | Stop hit or 4 weeks | Fund burner from an exchange |
| 8 Post-mortem | Live vs paper vs backtest | Decision recorded | Decide |

### Phase 4 strategies (fixed list)
1. **Launch snipe** baseline: buy every new token at T+latency; fixed TP / time exit. Expected to lose.
2. **Momentum filter**: buy after X buys and Y unique buyers in the first minute; trailing stop.
3. **Graduation play**: buy at 80–95% curve progress; sell around migration.
4. **Post-graduation pullback**: graduated tokens after 40–60% drawdown with volume; tight stop.
5. **Creator / holder filter** overlay on 2–4.
6. **Wallet following**: wallets consistently profitable in the design split (≥30 round
   trips, positive median trade); follow their buys at T+latency in later splits.

## 7. Go/no-go gate (all must pass)
| # | Criterion | Threshold |
| --- | --- | --- |
| 1 | Net PnL after costs, untouched test split | Positive |
| 2 | Same, latency doubled | Positive |
| 3 | Same, excluding single best trade | Positive |
| 4 | Test-split trades | ≥ 100 |
| 5 | 7-day paper vs backtest | Same sign, within 50% |
| 6 | Max drawdown, test + paper | < 40% of capital |

## 8. Live risk limits (enforced in code)
- $5 per trade ($2.50 first 3 days); max 2 open positions.
- Daily loss stop $10; total stop when balance ≤ $50 → kill switch until human reset.
- Priority fee + tip capped per transaction; skip the trade if exceeded.
- No trading if the data stream lagged > 3 s in the last minute.
- `scripts/flatten.py` sells everything independently of strategy code.

## 9. Budget
| Item | Cost |
| --- | --- |
| Droplet + weekly backups | ~$28.80/month |
| Claude Code | Included in Max |
| Data, monitoring, firewall, Telegram | $0 |
| Live capital | $100 max, Phase 7 only |
| Over 3 months, no-go case | ~$87 spent, $100 kept |

## 10. Timeline (from the day the droplet is up)
| When | Milestone |
| --- | --- |
| Day 0 | DigitalOcean setup (60–90 min); `/phase-run 1`; collector running |
| Days 1–3 | 72 h health check; Phase 2 starts on partial data |
| Week 2 | Phase 3 simulator |
| Day 14+ | Phase 4 research (needs 14 days of data) |
| Week 4 | Phase 5 paper trading (7 days) |
| ~Week 5 | **Go/no-go decision** |
| Weeks 6–9 | Live micro-trading if go |

## 11. Your weekly routine (about 30 minutes)
- Open the `pumplab` session at claude.ai/code. Run `/health` every couple of days.
- When a phase finishes, read its report (`docs/phase-reports/`), then `/phase-run` for the next.
- Never paste a private key, seed phrase or `.env` contents into any chat.
