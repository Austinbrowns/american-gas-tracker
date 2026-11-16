"""Fail the scheduled job when today's source snapshot is incomplete."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path
import sys

from .config import SOURCE_NAME, STATE_BY_ID
from .sources import parse_aaa_html, validate_source_records


def verify_daily_snapshot(project_root: Path | None = None, day: str | None = None) -> None:
    """Verify that the current run produced a complete 51-state snapshot."""

    root = project_root or Path(__file__).resolve().parent.parent
    snapshot_day = day or datetime.now(timezone.utc).date().isoformat()
    day_dir = root / "data" / "raw" / snapshot_day
    raw_path = day_dir / "aaa_state_prices.html.gz"
    results_path = day_dir / "source_results.json"
    status_path = root / "data" / "status.json"
    history_path = root / "data" / "history.csv"

    if not raw_path.exists():
        raise RuntimeError(f"No raw snapshot was written for {snapshot_day}")
    if not results_path.exists():
        raise RuntimeError(f"No source result was written for {snapshot_day}")

    results = json.loads(results_path.read_text(encoding="utf-8"))
    source = next((item for item in results.get("sources", []) if item.get("name") == SOURCE_NAME), None)
    if not source or not source.get("ok") or source.get("count") != len(STATE_BY_ID):
        raise RuntimeError(f"{SOURCE_NAME} did not produce all {len(STATE_BY_ID)} states: {source}")

    with gzip.open(raw_path, "rb") as compressed:
        records = parse_aaa_html(compressed.read())
    validate_source_records(records)

    with history_path.open("r", encoding="utf-8", newline="") as handle:
        history_rows = [row for row in csv.DictReader(handle) if row.get("date") == snapshot_day]
    if len(history_rows) != len(STATE_BY_ID):
        raise RuntimeError(
            f"History contains {len(history_rows)} rows for {snapshot_day}; expected {len(STATE_BY_ID)}"
        )

    status = json.loads(status_path.read_text(encoding="utf-8"))
    status_source = next(
        (item for item in status.get("sources", []) if item.get("name") == SOURCE_NAME),
        None,
    )
    if status.get("items") != len(STATE_BY_ID) or not status_source or status_source.get("ok") is not True:
        raise RuntimeError(f"status.json does not report a complete source run: {status}")


def main() -> None:
    try:
        verify_daily_snapshot()
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"Daily snapshot verification failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    print("Daily snapshot verified: 51 states recorded.")


if __name__ == "__main__":
    main()
