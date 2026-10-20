# pumplab

A research lab that measures whether any pump.fun trading rule makes money after
fees, using real on-chain data, before a single dollar is risked.

- Plan and all decisions: [`docs/BUILD_BRIEF.md`](docs/BUILD_BRIEF.md)
- Server setup (owner, once): [`docs/digitalocean-setup.md`](docs/digitalocean-setup.md)
- Rules for Claude Code: [`CLAUDE.md`](CLAUDE.md)
- Verified on-chain facts: [`docs/assumptions.md`](docs/assumptions.md)

## Status
| Phase | State |
| --- | --- |
| 0 Setup | Done 2026-10-20 |
| 1 Collect | Next: owner follows the DigitalOcean guide, then `/phase-run 1` |
| 2–8 | Not started |

## Commands (on the droplet)
```bash
uv run pytest -q
uv run python scripts/probe_logs.py 60      # live data check
uv run python scripts/health.py             # collector health
systemctl --user status pumplab-collector   # service
uv run python -m pumplab.store.rollup       # JSONL -> Parquet (timer runs it hourly)
```

No wallet, key or real money is used before Phase 7.
