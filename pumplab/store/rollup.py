"""Convert finished hourly JSON-lines files into Parquet (one file per event type
per hour), then gzip the raw file so disk use stays low. Raw data is never
deleted: `data/raw/<day>/<hour>.jsonl.gz` stays as the audit copy.

DuckDB can then query data/parquet/<Event>/**/*.parquet."""

from __future__ import annotations

import gzip
import shutil
from datetime import datetime, timezone
from pathlib import Path

import polars as pl


def _gzip_and_remove(src: Path) -> None:
    dst = src.with_suffix(".jsonl.gz")
    with src.open("rb") as fi, gzip.open(dst, "wb", compresslevel=6) as fo:
        shutil.copyfileobj(fi, fo)
    src.unlink()


def rollup(data_dir: Path) -> list[Path]:
    current = datetime.now(timezone.utc).strftime("%Y-%m-%d/%H")
    written: list[Path] = []
    for src in sorted((data_dir / "raw").glob("*/*.jsonl")):
        key = f"{src.parent.name}/{src.stem}"
        if key == current:
            continue  # still being written
        if src.stat().st_size == 0:
            src.unlink()
            continue
        df = pl.read_ndjson(src, infer_schema_length=None)
        for (ev,), part in df.group_by("event"):
            dst = data_dir / "parquet" / str(ev) / src.parent.name / f"{src.stem}.parquet"
            dst.parent.mkdir(parents=True, exist_ok=True)
            tmp = dst.with_suffix(".parquet.tmp")
            part.write_parquet(tmp)
            tmp.replace(dst)  # atomic: a crash never leaves a half-written file
            written.append(dst)
        _gzip_and_remove(src)
    return written


if __name__ == "__main__":
    from pumplab.config import load

    for p in rollup(load().data_dir):
        print(p)
