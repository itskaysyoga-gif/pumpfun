import gzip
import json

import duckdb

from pumplab.collector.stream import records_from_notification
from pumplab.store.rollup import rollup
from tests.test_config_and_collector import _notif


def test_rollup_writes_parquet_and_gzips_raw(tmp_path):
    src = tmp_path / "raw" / "2026-10-01" / "05.jsonl"
    src.parent.mkdir(parents=True)
    recs, _ = records_from_notification(_notif(), 1.0)
    src.write_text("\n".join(json.dumps(r) for r in recs * 3) + "\n")

    out = rollup(tmp_path)

    assert len(out) == 1 and out[0].name == "05.parquet"
    assert not src.exists()
    gz = src.with_suffix(".jsonl.gz")
    assert len(gzip.open(gz, "rt").read().splitlines()) == 3
    n = duckdb.sql(f"select count(*) from '{tmp_path}/parquet/TradeEvent/**/*.parquet'").fetchone()[0]
    assert n == 3
    assert rollup(tmp_path) == []  # idempotent: nothing left to do
