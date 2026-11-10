"""Daily pipeline entry point for the American gas-price tracker."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path
import os
from typing import Any

from tracker.history import build_history, raw_paths
from tracker.issues import build_issue_body, publish_daily_issue
from tracker.moves import appeared_and_disappeared, calculate_moves
from tracker.sources import fetch_aaa_html, parse_aaa_html, validate_source_records
from tracker.config import SOURCE_NAME, SOURCE_URL


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _raw_dates(raw_root: Path) -> list[str]:
    return sorted({path.parent.name for path in raw_paths(raw_root)})


def _load_history(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    import csv

    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _rows_for_date(rows: list[dict[str, Any]], day: str) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("date") == day]


def _previous_date(rows: list[dict[str, Any]], day: str) -> str | None:
    dates = sorted({row["date"] for row in rows if row.get("date") < day})
    return dates[-1] if dates else None


def run_pipeline(run_date: str | None = None, fetch: bool = True) -> dict[str, Any]:
    project_root = Path(__file__).resolve().parent
    day = run_date or datetime.now(timezone.utc).date().isoformat()
    datetime.strptime(day, "%Y-%m-%d")
    raw_root = project_root / "data" / "raw"
    day_dir = raw_root / day
    raw_path = day_dir / "aaa_state_prices.html.gz"
    source_result: dict[str, Any] = {"name": SOURCE_NAME, "url": SOURCE_URL, "ok": False, "count": 0}

    if fetch:
        try:
            body = fetch_aaa_html()
            records = parse_aaa_html(body)
            validate_source_records(records)
            day_dir.mkdir(parents=True, exist_ok=True)
            with gzip.open(raw_path, "wb") as compressed:
                compressed.write(body)
            source_result.update({"ok": True, "count": len(records), "format": "html"})
        except Exception as exc:  # The assignment requires a failed source not to stop the run.
            if raw_path.exists():
                raw_path.unlink()
            source_result["error"] = f"{type(exc).__name__}: {exc}"
    else:
        if raw_path.exists():
            try:
                with gzip.open(raw_path, "rb") as compressed:
                    count = len(parse_aaa_html(compressed.read()))
                source_result.update({"ok": True, "count": count})
            except Exception as exc:
                source_result["error"] = f"{type(exc).__name__}: {exc}"
        else:
            source_result["error"] = "fetch skipped and no raw file exists for this date"

    day_dir.mkdir(parents=True, exist_ok=True)
    _write_json(day_dir / "source_results.json", {"run_date": day, "sources": [source_result]})

    history_path = project_root / "data" / "history.csv"
    rows = build_history(raw_root, history_path)
    current = _rows_for_date(rows, day)
    prior_day = _previous_date(rows, day)
    previous = _rows_for_date(rows, prior_day) if prior_day else []
    moves = calculate_moves(previous, current)
    new_items, gone_items = appeared_and_disappeared(previous, current)
    dates = _raw_dates(raw_root)
    run_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    status = {
        "run_time": run_time,
        "first_run_date": dates[0] if dates else None,
        "days_with_success": len(dates),
        "items": len(current),
        "new_today": new_items,
        "gone_today": gone_items,
        "sources": [{key: source_result[key] for key in ("name", "ok", "count")}],
    }
    _write_json(project_root / "data" / "status.json", status)

    issue_body = build_issue_body(day, moves, new_items, gone_items, [source_result])
    (project_root / "data" / "issue.md").write_text(issue_body, encoding="utf-8")
    try:
        issue_result = publish_daily_issue(day, issue_body, os.getenv("GITHUB_TOKEN"), os.getenv("GITHUB_REPOSITORY"))
    except Exception as exc:  # An Issue outage must not prevent the data commit.
        issue_result = f"failed: {type(exc).__name__}: {exc}"

    return {"status": status, "issue": issue_result, "history_rows": len(rows), "moves": moves}


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch AAA prices, rebuild history, publish status, and open the daily Issue")
    parser.add_argument("--date", help="UTC date override used for testing, in YYYY-MM-DD format")
    parser.add_argument("--skip-fetch", action="store_true", help="Do not call AAA; rebuild from existing raw files")
    args = parser.parse_args()
    result = run_pipeline(args.date, fetch=not args.skip_fetch)
    print(json.dumps(result["status"], indent=2))
    print(f"History rows: {result['history_rows']}")
    print(f"Issue: {result['issue']}")


if __name__ == "__main__":
    main()

