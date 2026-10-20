---
name: health
description: Check that the pumplab data collector on this server is healthy (service up, fresh data, gap time, disk) and fix common problems. Use when the owner asks "/health", "is the collector ok", "status" or before starting any analysis phase.
argument-hint: "[hours, default 24]"
model: sonnet
effort: low
allowed-tools: Bash(uv run python scripts/health.py*) Bash(systemctl --user status *) Bash(journalctl --user *) Bash(df -h*)
---

# Collector health check

1. Run `uv run python scripts/health.py --hours N`, where N is the number in "$ARGUMENTS"
   if one was given, otherwise 24.
2. If STATUS is OK: reply in 3 lines (service, trades in window, gap %, disk free).
3. If ATTENTION:
   - Service not active: `journalctl --user -u pumplab-collector -n 50 --no-pager`, find the
     error, then `systemctl --user restart pumplab-collector` and re-check after 2 minutes.
   - No new data but service active: check the journal for subscribe/RPC errors. Repeated
     disconnects from the public RPC mean the owner should create a free Helius key; say
     so in one line and do not change RPC settings yourself.
   - Gap time > 1%: list the gaps from `data/gaps.jsonl` (start, end, reason).
   - Disk < 15% free: check `du -sh data/*`. Run the rollup
     (`uv run python -m pumplab.store.rollup`) if raw `.jsonl` files are piling up.
     Never delete data without asking the owner.
4. Never read `.env`. Never change code in this skill; report code problems instead.
