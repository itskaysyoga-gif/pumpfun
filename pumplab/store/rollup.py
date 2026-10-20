"""Convert finished hourly JSON-lines files into Parquet (one file per event type
per hour) and delete nothing. DuckDB can then query data/parquet/**.parquet."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import polars as pl


def rollup(data_dir: Path) -> list[Path]:
    current = datetime.now(timezone.utc).strftime("%Y-%m-%d/%H")
    written: list[Path] = []
    for src in sorted((data_dir / "raw").glob("*/*.jsonl")):
        key = f"{src.parent.name}/{src.stem}"
        if key == current:
            continue  # still being written
        df = pl.read_ndjson(src, infer_schema_length=None)
        for (ev,), part in df.group_by("event"):
            dst = data_dir / "parquet" / ev / src.parent.name / f"{src.stem}.parquet"
            if dst.exists():
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            part.write_parquet(dst)
            written.append(dst)
    return written


if __name__ == "__main__":
    from pumplab.config import load

    for p in rollup(load().data_dir):
        print(p)
