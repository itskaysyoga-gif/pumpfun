# pumplab

A research lab that measures whether any pump.fun trading rule makes money after
fees, using real on-chain data, before a single dollar is risked.

- Plan: [`docs/BUILD_BRIEF.md`](docs/BUILD_BRIEF.md)
- Rules for Claude Code: [`CLAUDE.md`](CLAUDE.md)
- Verified on-chain facts: [`docs/assumptions.md`](docs/assumptions.md)
- Server setup: [`docs/vm-setup.md`](docs/vm-setup.md)

## Status
| Phase | State |
| --- | --- |
| 0 Setup | Done 2026-10-20 |
| 1 Collect | Next: owner sets up VM and runs the 60-second probe |
| 2–8 | Not started |

## Local commands
```bash
uv sync
uv run pytest -q
uv run python scripts/probe_logs.py 60     # live data check (needs Solana RPC access)
uv run python scripts/run_collector.py     # collector (run under systemd on the VM)
uv run python -m pumplab.store.rollup      # JSONL -> Parquet
```

No wallet, key or real money is used before Phase 7.
