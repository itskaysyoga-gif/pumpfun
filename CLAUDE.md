# pumplab — rules for Claude Code

You are building a research lab that tests pump.fun trading rules before any real
money is used. Default assumption: strategies lose. A "no-go" result is a success.
The full plan is `docs/BUILD_BRIEF.md`. Current status is in `README.md`.

## Hard rules (never break; stop and ask if a task conflicts)
- Never clone, install or run third-party trading/sniper bot code (GitHub, npm, PyPI).
  Reading official pump.fun docs/IDLs is fine. Malware-laced "sniper bots" are common.
- Only dependencies already in `pyproject.toml`. Ask the owner before adding any other,
  with name, publisher and weekly downloads.
- Never ask for, read, print, log or commit a private key or seed phrase.
- No transaction-signing code before Phase 7 is approved in writing by the owner.
- Live trading requires `LIVE=1` AND `WALLET_PUBKEY` set AND matching the configured
  burner. Anything else runs simulated. Enforced in `pumplab/config.py`.
- All risk limits live in `pumplab/risk/` and cannot be bypassed by strategy code.
- Verify program IDs, fees and endpoints from official sources (`docs/idl/`,
  github.com/pump-fun/pump-public-docs). Record in `docs/assumptions.md` with URL + date.
  Never hardcode from memory.
- Fees are dynamic (market-cap tiers). Use the actual `fee` + `creator_fee` from each
  TradeEvent; never assume a flat percentage.
- No token launching, wash trading, copy-trading private paid groups, or manipulation.

## Environment
- You run as Linux user `pumplab` on a DigitalOcean droplet (FRA1), usually driven by the
  owner from claude.ai/code via Remote Control. No sudo. Services are `systemctl --user`.
- Collector: `pumplab-collector.service`; rollup: `pumplab-rollup.timer`. Data in `./data`.
- Use the skills: `/phase-run`, `/health`, `/backtest-report`; the `reviewer` subagent
  checks money-related code and results.
- Default model is Opus (set in `.claude/settings.json`). The owner may switch to Sonnet
  for routine work if usage limits get tight.

## Working style
- One phase at a time. Stop at each phase's "done when" criteria and write
  `docs/phase-reports/phase-N.md`: what was built, results with numbers, open issues.
- Tests first for the decoder, simulator and risk manager.
- Report numbers honestly, including bad ones. Never tune on the held-out test split.
- Keep the owner's time low: short updates, one decision asked at a time.
- Do not spend money (paid RPC, paid data, bigger VM) without owner approval.
