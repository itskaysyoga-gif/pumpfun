"""Minimal Borsh decoder driven by an Anchor IDL (no third-party deps).

pump.fun appends new fields to its events over time, so older events are
shorter than the current IDL. Decoding is tolerant: when the bytes run out at a
field boundary, the remaining fields are returned as None.
"""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58encode(b: bytes) -> str:
    n = int.from_bytes(b, "big")
    out = ""
    while n:
        n, r = divmod(n, 58)
        out = _B58[r] + out
    pad = len(b) - len(b.lstrip(b"\0"))
    return "1" * pad + out


def b58decode(s: str) -> bytes:
    n = 0
    for c in s:
        n = n * 58 + _B58.index(c)
    body = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    pad = len(s) - len(s.lstrip("1"))
    return b"\0" * pad + body


class Truncated(Exception):
    pass


_PRIM = {
    "bool": ("<?", 1),
    "u8": ("<B", 1),
    "i8": ("<b", 1),
    "u16": ("<H", 2),
    "i16": ("<h", 2),
    "u32": ("<I", 4),
    "i32": ("<i", 4),
    "u64": ("<Q", 8),
    "i64": ("<q", 8),
    "f32": ("<f", 4),
    "f64": ("<d", 8),
}


@dataclass
class _Reader:
    buf: bytes
    pos: int = 0

    def take(self, n: int) -> bytes:
        if self.pos + n > len(self.buf):
            raise Truncated
        b = self.buf[self.pos : self.pos + n]
        self.pos += n
        return b

    @property
    def done(self) -> bool:
        return self.pos >= len(self.buf)


class IdlDecoder:
    def __init__(self, idl: dict):
        self.types = {t["name"]: t["type"] for t in idl.get("types", [])}
        self.events = {bytes(e["discriminator"]): e["name"] for e in idl.get("events", [])}

    @classmethod
    def from_file(cls, path: str | Path) -> "IdlDecoder":
        return cls(json.loads(Path(path).read_text()))

    # --- public -----------------------------------------------------------
    def decode_event(self, data: bytes) -> tuple[str, dict[str, Any]] | None:
        """data = 8-byte discriminator + borsh body. Returns (name, fields) or None."""
        name = self.events.get(data[:8])
        if name is None:
            return None
        r = _Reader(data[8:])
        return name, self._struct_fields(self.types[name]["fields"], r, tolerant=True)

    # --- internals --------------------------------------------------------
    def _struct_fields(self, fields: list, r: _Reader, tolerant: bool = False) -> dict:
        out: dict[str, Any] = {}
        for i, f in enumerate(fields):
            if tolerant and r.done:
                for rest in fields[i:]:
                    out[rest["name"]] = None
                break
            out[f["name"]] = self._value(f["type"], r)
        return out

    def _value(self, t: Any, r: _Reader) -> Any:
        if isinstance(t, str):
            if t in _PRIM:
                fmt, n = _PRIM[t]
                return struct.unpack(fmt, r.take(n))[0]
            if t in ("u128", "i128"):
                return int.from_bytes(r.take(16), "little", signed=t == "i128")
            if t == "pubkey":
                return b58encode(r.take(32))
            if t == "string":
                (ln,) = struct.unpack("<I", r.take(4))
                return r.take(ln).decode("utf-8", "replace")
            if t == "bytes":
                (ln,) = struct.unpack("<I", r.take(4))
                return r.take(ln).hex()
            raise ValueError(f"unsupported type {t}")
        if "option" in t:
            return self._value(t["option"], r) if r.take(1)[0] else None
        if "vec" in t:
            (ln,) = struct.unpack("<I", r.take(4))
            return [self._value(t["vec"], r) for _ in range(ln)]
        if "array" in t:
            inner, n = t["array"]
            return [self._value(inner, r) for _ in range(n)]
        if "defined" in t:
            return self._defined(self.types[t["defined"]["name"]], r)
        raise ValueError(f"unsupported type {t}")

    def _defined(self, td: dict, r: _Reader) -> Any:
        if td["kind"] == "struct":
            return self._struct_fields(td["fields"], r)
        if td["kind"] == "enum":
            idx = r.take(1)[0]
            variant = td["variants"][idx]
            fields = variant.get("fields")
            if not fields:
                return variant["name"]
            if isinstance(fields[0], dict) and "name" in fields[0]:
                return {variant["name"]: self._struct_fields(fields, r)}
            return {variant["name"]: [self._value(f, r) for f in fields]}
        raise ValueError(f"unsupported kind {td['kind']}")
