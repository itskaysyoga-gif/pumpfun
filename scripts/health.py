"""Collector health report. Prints plain text; exits 1 if something needs attention.

Usage:  uv run python scripts/health.py [--hours 24]
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from pumplab.config import load


def service_state() -> str:
    try:
        out = subprocess.run(
            ["systemctl", "--user", "is-active", "pumplab-collector"],
            capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip() or out.stderr.strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return f"unknown ({e})"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=24)
    args = ap.parse_args()
    s = load()
    d = Path(s.data_dir)
    now = time.time()
    problems: list[str] = []

    state = service_state()
    print(f"service: {state}")
    if state != "active":
        problems.append("collector service is not active")

    raw = sorted((d / "raw").glob("*/*.jsonl"))
    if raw:
        age = now - raw[-1].stat().st_mtime
        print(f"newest raw file: {raw[-1].relative_to(d)}  (last write {age:.0f}s ago)")
        if age > 120:
            problems.append(f"no new data for {age/60:.0f} min")
    else:
        print("newest raw file: none")
        problems.append("no raw data yet")

    gap_s = 0.0
    gaps = d / "gaps.jsonl"
    if gaps.exists():
        since = now - args.hours * 3600
        for line in gaps.read_text().splitlines():
            g = json.loads(line)
            if g["end"] >= since:
                gap_s += g["end"] - max(g["start"], since)
    pct = 100 * gap_s / (args.hours * 3600)
    print(f"gap time, last {args.hours:.0f}h: {gap_s/60:.1f} min ({pct:.2f}%)")
    if pct > 1:
        problems.append(f"gap time {pct:.2f}% > 1%")

    pq = d / "parquet"
    if pq.exists():
        try:
            import duckdb

            q = f"""select count(*) from read_parquet('{pq}/TradeEvent/**/*.parquet')
                    where recv_ts > {now - args.hours * 3600}"""
            n = duckdb.sql(q).fetchone()[0]
            print(f"trades in parquet, last {args.hours:.0f}h: {n:,}")
        except Exception as e:  # noqa: BLE001
            print(f"parquet query skipped: {e}")

    du = shutil.disk_usage(d if d.exists() else Path("."))
    free_pct = 100 * du.free / du.total
    data_gb = sum(p.stat().st_size for p in d.rglob("*") if p.is_file()) / 1e9 if d.exists() else 0
    print(f"disk: {du.free/1e9:.1f} GB free ({free_pct:.0f}%), data dir {data_gb:.2f} GB")
    if free_pct < 15:
        problems.append(f"disk only {free_pct:.0f}% free")

    print("\nSTATUS:", "OK" if not problems else "ATTENTION: " + "; ".join(problems))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
