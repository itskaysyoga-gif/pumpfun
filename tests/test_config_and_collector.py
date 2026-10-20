import base64
import json

from pumplab.collector.stream import HourlyWriter, records_from_notification
from pumplab.config import Settings
from pumplab.constants import PUMP_PROGRAM_ID
from tests.test_decode import _trade_event_bytes


def test_live_guard_defaults_off():
    assert Settings(_env_file=None).live_trading_enabled is False


def test_live_guard_needs_all_three():
    base = dict(_env_file=None, live=True, wallet_pubkey="A", approved_burner_pubkey="A")
    assert Settings(**base).live_trading_enabled is True
    assert Settings(**{**base, "live": False}).live_trading_enabled is False
    assert Settings(**{**base, "wallet_pubkey": "B"}).live_trading_enabled is False
    assert Settings(**{**base, "approved_burner_pubkey": ""}).live_trading_enabled is False


def _notif(err=None):
    data = base64.b64encode(_trade_event_bytes()).decode()
    return {
        "method": "logsNotification",
        "params": {
            "result": {
                "context": {"slot": 123},
                "value": {
                    "signature": "sig1",
                    "err": err,
                    "logs": [f"Program {PUMP_PROGRAM_ID} invoke [1]", f"Program data: {data}", f"Program {PUMP_PROGRAM_ID} success"],
                },
            }
        },
    }


def test_notification_to_records(tmp_path):
    recs, st = records_from_notification(_notif(), 1.0)
    assert st == {"tx": 1, "failed": 0, "tx_without_events": 0}
    assert recs[0]["event"] == "TradeEvent" and recs[0]["slot"] == 123
    w = HourlyWriter(tmp_path)
    w.write(recs[0])
    w.close()
    line = next((tmp_path / "raw").glob("*/*.jsonl")).read_text().strip()
    assert json.loads(line)["sig"] == "sig1"


def test_failed_tx_skipped():
    recs, st = records_from_notification(_notif(err={"InstructionError": [0, "x"]}), 1.0)
    assert recs == [] and st["failed"] == 1
