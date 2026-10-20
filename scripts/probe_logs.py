"""Phase 1, step 1: 60-second live probe. Run this on the VM before anything else.

It answers three questions the whole plan depends on:
  1. Does this RPC accept logsSubscribe on the pump.fun program?
  2. Do pump.fun events appear as 'Program data:' log lines (decodable here)?
  3. How much data per second is this (to size RPC usage)?

Usage:  uv run python scripts/probe_logs.py [seconds]
"""

import asyncio
import collections
import json
import sys
import time

import websockets

from pumplab.collector.stream import records_from_notification, subscribe_msg
from pumplab.config import load
from pumplab.constants import WSOL_MINT


async def main(seconds: float) -> None:
    s = load()
    print(f"Connecting to {s.rpc_ws_url} for {seconds:.0f}s ...")
    counts = collections.Counter()
    ix_names = collections.Counter()
    quote = collections.Counter()
    nbytes = 0
    async with websockets.connect(s.rpc_ws_url, max_size=2**24) as ws:
        await ws.send(subscribe_msg())
        print("subscribe reply:", await asyncio.wait_for(ws.recv(), 15))
        t0 = time.time()
        while time.time() - t0 < seconds:
            try:
                raw = await asyncio.wait_for(ws.recv(), 5)
            except asyncio.TimeoutError:
                continue
            nbytes += len(raw)
            msg = json.loads(raw)
            if msg.get("method") != "logsNotification":
                continue
            recs, st = records_from_notification(msg, time.time())
            counts.update(st)
            for r in recs:
                counts["ev_" + r["event"]] += 1
                if r["event"] == "TradeEvent":
                    ix_names[r.get("ix_name")] += 1
                    quote["SOL" if r.get("quote_mint") in (None, WSOL_MINT) else "other"] += 1
    el = seconds
    ok_tx = counts["tx"] - counts["failed"]
    print("\n=== RESULT ===")
    print(f"transactions/s: {counts['tx']/el:.1f}  (failed: {counts['failed']})")
    print(f"successful tx with NO decodable event: {counts['tx_without_events']} of {ok_tx}")
    print("events:", {k: v for k, v in counts.items() if k.startswith('ev_')})
    print("trade ix names:", dict(ix_names))
    print("trade quote mints:", dict(quote))
    print(f"bandwidth: {nbytes/el/1024:.0f} KB/s  ~= {nbytes/el*86400/1e9:.1f} GB/day")
    if ok_tx and counts["tx_without_events"] / ok_tx > 0.5:
        print("\nWARNING: most tx had no 'Program data' events. Events are probably")
        print("emitted only via self-CPI. Tell Claude: the collector must switch to")
        print("transaction fetching / gRPC. Do not proceed with Phase 1 as-is.")
    elif counts["ev_TradeEvent"] == 0:
        print("\nWARNING: no trades decoded. Check RPC URL and IDL.")
    else:
        print("\nOK: log-based collection works on this RPC.")


if __name__ == "__main__":
    asyncio.run(main(float(sys.argv[1]) if len(sys.argv) > 1 else 60))
