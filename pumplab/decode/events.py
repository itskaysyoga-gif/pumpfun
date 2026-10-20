"""Turn Solana log lines / inner-instruction data into pump.fun events."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Iterable

from pumplab.constants import ANCHOR_EVENT_IX_TAG, PUMP_PROGRAM_ID
from pumplab.decode.idl_borsh import IdlDecoder

IDL_PATH = Path(__file__).resolve().parents[2] / "docs" / "idl" / "pump.json"

_decoder: IdlDecoder | None = None


def decoder() -> IdlDecoder:
    global _decoder
    if _decoder is None:
        _decoder = IdlDecoder.from_file(IDL_PATH)
    return _decoder


def decode_event_bytes(raw: bytes) -> tuple[str, dict[str, Any]] | None:
    """Accepts either plain event bytes (disc + body) or a self-CPI event
    instruction (8-byte Anchor tag + disc + body)."""
    if raw[:8] == ANCHOR_EVENT_IX_TAG:
        raw = raw[8:]
    return decoder().decode_event(raw)


def events_from_logs(logs: Iterable[str]) -> list[tuple[str, dict[str, Any]]]:
    """Extract events from 'Program data: <base64>' lines emitted while the pump
    program is the active program. Lines from other programs are ignored."""
    out: list[tuple[str, dict[str, Any]]] = []
    stack: list[str] = []
    for line in logs:
        if line.startswith("Program ") and " invoke [" in line:
            stack.append(line.split()[1])
        elif line.startswith("Program ") and (line.endswith(" success") or " failed" in line):
            if stack:
                stack.pop()
        elif line.startswith("Program data: ") and stack and stack[-1] == PUMP_PROGRAM_ID:
            try:
                raw = base64.b64decode(line[len("Program data: ") :])
            except ValueError:
                continue
            ev = decode_event_bytes(raw)
            if ev:
                out.append(ev)
    return out
