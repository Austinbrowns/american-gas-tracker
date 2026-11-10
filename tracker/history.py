"""Rebuild data/history.csv from compressed raw files only."""

from __future__ import annotations

import argparse
import csv
import gzip
from pathlib import Path
from typing import Any

from .config import HISTORY_COLUMNS, NUMERIC_COLUMNS, SOURCE_NAME
from .sources import parse_aaa_html


def raw_paths(raw_root: Path) -> list[Path]:
    return sorted(raw_root.glob("*/aaa_state_prices.html.gz"))


def _format_value(value: Any) -> str:
    if value is None or value == "":
        return ""
    return f"{float(value):.4f}"


def read_raw_file(path: Path) -> list[dict[str, Any]]:
    date = path.parent.name
    with gzip.open(path, "rb") as compressed:
        parsed = parse_aaa_html(compressed.read())
    rows: list[dict[str, Any]] = []
    for record in parsed:
        row = {
            "date": date,
            "item_id": record["item_id"],
            "item": record["item"],
            "source": SOURCE_NAME,
            "region": record["region"],
        }
        row.update({column: _format_value(record.get(column)) for column in NUMERIC_COLUMNS})
        rows.append(row)
    return rows


def build_history(raw_root: Path, output_path: Path) -> list[dict[str, Any]]:
    """Rebuild the complete history deterministically and return its rows."""

    rows: list[dict[str, Any]] = []
    for path in raw_paths(raw_root):
        rows.extend(read_raw_file(path))
    rows.sort(key=lambda row: (row["date"], row["item_id"]))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HISTORY_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return rows


def load_history(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild history.csv from compressed raw files")
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--output", type=Path, default=Path("data/history.csv"))
    args = parser.parse_args()
    rows = build_history(args.raw_dir, args.output)
    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()

