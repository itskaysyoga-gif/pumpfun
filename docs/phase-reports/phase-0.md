# Phase 0 report — 2026-10-20

## Built
- Repo scaffold, `CLAUDE.md`, pinned deps (`uv.lock`), `.env.example`, `.gitignore`.
- Official pump IDL copied to `docs/idl/pump.json` (pump-public-docs @ 639b87f, 2026-10-13).
- IDL-driven Borsh decoder with no extra dependencies; tolerates older, shorter events;
  accepts both log and self-CPI event forms.
- Phase 1 collector (logsSubscribe, hourly JSONL, gap log, watchdog, Telegram), 60-second
  probe, Parquet rollup, systemd unit, VM setup guide.
- 10 tests passing (decoder, log parsing, live-trading guard, collector records, writer).

## Findings that changed the plan
- pump.fun changed a lot in 2025–26: dynamic fee tiers, v2/v3 trade instructions,
  synthetic migration, coins quoted in USDC or other pump coins, cashback deprecated.
  Older GitHub bots are almost certainly broken.
- PumpPortal's per-token trade stream is metered (0.01 SOL / 10k events); too costly
  as the main feed. Using standard Solana `logsSubscribe` instead.
- Fees must be read per trade from events, not assumed.
- Added strategy 6 (following consistently profitable public wallets).
- Vercel is not useful for this project.

## Not verified (blocks Phase 1)
- Whether events appear as `Program data:` log lines on the chosen RPC, and data volume.
  The sandbox that built Phase 0 cannot reach Solana RPC. Run `scripts/probe_logs.py`
  on the VM.

## Next
Owner: VM setup + probe (`docs/vm-setup.md` steps 1–4). Paste probe output to Claude.
