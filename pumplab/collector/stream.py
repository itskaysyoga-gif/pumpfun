"""Phase 1 collector: stream every pump.fun program log via Solana `logsSubscribe`,
decode Create/Trade/Complete events, and append them to hourly JSON-lines files.

Gaps (disconnects, silence) are recorded so backtests can exclude them.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import websockets

from pumplab.constants import PUMP_PROGRAM_ID
from pumplab.decode.events import events_from_logs

log = logging.getLogger("pumplab.collector")

SILENCE_SECONDS = 60  # pump.fun never goes quiet this long; treat as a dead stream


def subscribe_msg() -> str:
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "logsSubscribe",
            "params": [{"mentions": [PUMP_PROGRAM_ID]}, {"commitment": "confirmed"}],
        }
    )


def _jsonable(v: Any) -> Any:
    return str(v) if isinstance(v, int) and abs(v) > 2**53 else v


def records_from_notification(msg: dict, recv_ts: float) -> tuple[list[dict], dict]:
    """Returns (event records, stats) for one logsNotification message."""
    value = msg["params"]["result"]["value"]
    slot = msg["params"]["result"]["context"]["slot"]
    stats = {"tx": 1, "failed": 0, "tx_without_events": 0}
    if value.get("err") is not None:
        stats["failed"] = 1
        return [], stats
    events = events_from_logs(value.get("logs") or [])
    if not events:
        stats["tx_without_events"] = 1
    recs = []
    for i, (name, fields) in enumerate(events):
        recs.append(
            {
                "event": name,
                "slot": slot,
                "sig": value["signature"],
                "idx": i,
                "recv_ts": round(recv_ts, 3),
                **{k: _jsonable(v) for k, v in fields.items() if k != "shareholders"},
            }
        )
    return recs, stats


@dataclass
class HourlyWriter:
    root: Path
    _fh: Any = None
    _key: str = ""

    def write(self, rec: dict) -> None:
        now = datetime.now(timezone.utc)
        key = now.strftime("%Y-%m-%d/%H")
        if key != self._key:
            if self._fh:
                self._fh.close()
            path = self.root / "raw" / f"{key}.jsonl"
            path.parent.mkdir(parents=True, exist_ok=True)
            self._fh = path.open("a", buffering=1)
            self._key = key
        self._fh.write(json.dumps(rec, separators=(",", ":")) + "\n")

    def close(self) -> None:
        if self._fh:
            self._fh.close()


@dataclass
class Collector:
    ws_url: str
    data_dir: Path
    alert: Callable[[str], None] = lambda m: None
    stats: dict = field(default_factory=lambda: {"tx": 0, "failed": 0, "tx_without_events": 0, "events": 0})

    def _gap(self, start: float, end: float, reason: str) -> None:
        p = self.data_dir / "gaps.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a") as f:
            f.write(json.dumps({"start": start, "end": end, "reason": reason}) + "\n")

    async def run(self, stop_after: float | None = None) -> None:
        writer = HourlyWriter(self.data_dir)
        backoff = 1.0
        last_msg = time.time()
        t0 = time.time()
        try:
            while stop_after is None or time.time() - t0 < stop_after:
                down_since = time.time()
                try:
                    async with websockets.connect(self.ws_url, max_size=2**24, ping_interval=20) as ws:
                        await ws.send(subscribe_msg())
                        ack = json.loads(await asyncio.wait_for(ws.recv(), 15))
                        if "error" in ack:
                            raise RuntimeError(f"subscribe rejected: {ack['error']}")
                        if down_since - last_msg > 2:
                            self._gap(last_msg, time.time(), "reconnect")
                        log.info("subscribed (id %s)", ack.get("result"))
                        backoff = 1.0
                        while stop_after is None or time.time() - t0 < stop_after:
                            raw = await asyncio.wait_for(ws.recv(), SILENCE_SECONDS)
                            now = time.time()
                            last_msg = now
                            msg = json.loads(raw)
                            if msg.get("method") != "logsNotification":
                                continue
                            recs, st = records_from_notification(msg, now)
                            for k, v in st.items():
                                self.stats[k] += v
                            for r in recs:
                                writer.write(r)
                            self.stats["events"] += len(recs)
                except asyncio.TimeoutError:
                    self.alert(f"pumplab: no data for {SILENCE_SECONDS}s, reconnecting")
                    log.warning("silence timeout; reconnecting")
                except Exception as e:  # noqa: BLE001 - keep the collector alive
                    log.warning("stream error: %s; retry in %.0fs", e, backoff)
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, 60)
        finally:
            writer.close()
