"""Run the Phase 1 collector forever (systemd keeps it alive).

Usage:  uv run python scripts/run_collector.py
"""

import asyncio
import logging

from pumplab.alerts import make_alert
from pumplab.collector.stream import Collector
from pumplab.config import load

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def main() -> None:
    s = load()
    alert = make_alert(s.telegram_bot_token, s.telegram_chat_id)
    alert("pumplab collector starting")
    asyncio.run(Collector(s.rpc_ws_url, s.data_dir, alert).run())


if __name__ == "__main__":
    main()
