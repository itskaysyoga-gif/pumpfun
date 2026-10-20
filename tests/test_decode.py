import base64
import struct

from pumplab.constants import ANCHOR_EVENT_IX_TAG, PUMP_PROGRAM_ID, WSOL_MINT
from pumplab.decode.events import decode_event_bytes, decoder, events_from_logs
from pumplab.decode.idl_borsh import b58decode, b58encode

MINT = "So11111111111111111111111111111111111111112"
USER = "11111111111111111111111111111111"


def _trade_event_bytes(truncate_after_creator_fee: bool = False) -> bytes:
    disc = next(d for d, n in decoder().events.items() if n == "TradeEvent")
    pk = lambda s: b58decode(s).rjust(32, b"\0")  # noqa: E731
    body = b"".join(
        [
            pk(MINT),
            struct.pack("<Q", 1_000_000_000),  # sol_amount
            struct.pack("<Q", 35_000_000_000_000),  # token_amount
            struct.pack("<?", True),  # is_buy
            pk(USER),
            struct.pack("<q", 1_760_000_000),
            struct.pack("<Q", 31_000_000_000),
            struct.pack("<Q", 1_038_000_000_000_000),
            struct.pack("<Q", 1_000_000_000),
            struct.pack("<Q", 758_000_000_000_000),
            pk(USER),  # fee_recipient
            struct.pack("<Q", 95),
            struct.pack("<Q", 9_500_000),  # fee
            pk(USER),  # creator
            struct.pack("<Q", 30),
            struct.pack("<Q", 3_000_000),  # creator_fee
        ]
    )
    if truncate_after_creator_fee:
        return disc + body
    rest = b"".join(
        [
            struct.pack("<?", True),
            struct.pack("<Q", 0),
            struct.pack("<Q", 0),
            struct.pack("<Q", 0),
            struct.pack("<q", 0),
            struct.pack("<I", 6) + b"buy_v3",
            struct.pack("<?", False),
            struct.pack("<Q", 0),
            struct.pack("<Q", 0),
            struct.pack("<Q", 0),
            struct.pack("<Q", 0),
            struct.pack("<I", 1) + pk(USER) + struct.pack("<H", 10000),  # shareholders
            pk(WSOL_MINT),
            struct.pack("<Q", 1_000_000_000),
            struct.pack("<Q", 0),
            struct.pack("<Q", 0),
            struct.pack("<Q", 0),
            struct.pack("<Q", 0),
            struct.pack("<Q", 0),
        ]
    )
    return disc + body + rest


def test_b58_roundtrip():
    for s in (MINT, USER, PUMP_PROGRAM_ID):
        assert b58encode(b58decode(s).rjust(32, b"\0")) == s


def test_full_trade_event():
    name, f = decode_event_bytes(_trade_event_bytes())
    assert name == "TradeEvent"
    assert f["mint"] == MINT and f["is_buy"] is True
    assert f["sol_amount"] == 1_000_000_000 and f["fee"] == 9_500_000
    assert f["ix_name"] == "buy_v3" and f["quote_mint"] == WSOL_MINT
    assert f["shareholders"] == [{"address": USER, "share_bps": 10000}]


def test_older_shorter_event_is_tolerated():
    name, f = decode_event_bytes(_trade_event_bytes(truncate_after_creator_fee=True))
    assert name == "TradeEvent"
    assert f["creator_fee"] == 3_000_000
    assert f["ix_name"] is None and f["quote_mint"] is None


def test_self_cpi_tag_is_stripped():
    name, _ = decode_event_bytes(ANCHOR_EVENT_IX_TAG + _trade_event_bytes())
    assert name == "TradeEvent"


def test_logs_only_from_pump_program():
    data = base64.b64encode(_trade_event_bytes()).decode()
    logs = [
        "Program ComputeBudget111111111111111111111111111111 invoke [1]",
        "Program ComputeBudget111111111111111111111111111111 success",
        f"Program {PUMP_PROGRAM_ID} invoke [1]",
        "Program log: Instruction: Buy",
        f"Program data: {data}",
        f"Program {PUMP_PROGRAM_ID} success",
        "Program OtherProgram11111111111111111111111111111 invoke [1]",
        f"Program data: {data}",  # same bytes but not from pump: must be ignored
        "Program OtherProgram11111111111111111111111111111 success",
    ]
    evs = events_from_logs(logs)
    assert [n for n, _ in evs] == ["TradeEvent"]


def test_unknown_discriminator_ignored():
    assert decode_event_bytes(b"\x00" * 40) is None
