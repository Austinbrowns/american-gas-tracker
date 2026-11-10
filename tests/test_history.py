import gzip
from pathlib import Path

from tracker.history import build_history


DAY_ONE = b"""
<table><tr><th>State</th><th>Regular</th><th>Mid-Grade</th><th>Premium</th><th>Diesel</th></tr>
<tr><td>Alabama</td><td>$3.1000</td><td>$3.5000</td><td>$3.9000</td><td>$4.2000</td></tr>
<tr><td>Texas</td><td>$3.2000</td><td>$3.6000</td><td>$4.0000</td><td>$4.3000</td></tr></table>
"""

DAY_TWO = b"""
<table><tr><th>State</th><th>Regular</th><th>Mid-Grade</th><th>Premium</th><th>Diesel</th></tr>
<tr><td>Alabama</td><td>$3.1500</td><td>$3.5500</td><td>$3.9500</td><td>$4.2500</td></tr>
<tr><td>Texas</td><td>$3.1800</td><td>$3.5800</td><td>$3.9800</td><td>$4.2800</td></tr></table>
"""


def write_raw(root: Path, day: str, payload: bytes) -> None:
    folder = root / day
    folder.mkdir(parents=True)
    with gzip.open(folder / "aaa_state_prices.html.gz", "wb") as output:
        output.write(payload)


def test_history_is_sorted_and_built_from_raw_files(tmp_path):
    raw = tmp_path / "raw"
    write_raw(raw, "2026-01-02", DAY_TWO)
    write_raw(raw, "2026-01-01", DAY_ONE)
    output = tmp_path / "history.csv"

    rows = build_history(raw, output)

    assert len(rows) == 4
    assert [(row["date"], row["item_id"]) for row in rows] == [
        ("2026-01-01", "AL"),
        ("2026-01-01", "TX"),
        ("2026-01-02", "AL"),
        ("2026-01-02", "TX"),
    ]
    assert rows[2]["regular_usd_per_gallon"] == "3.1500"
    assert output.read_text(encoding="utf-8").splitlines()[0].startswith("date,item_id,item,source,region")


def test_second_run_same_day_replaces_the_raw_snapshot(tmp_path):
    raw = tmp_path / "raw"
    output = tmp_path / "history.csv"
    write_raw(raw, "2026-01-01", DAY_ONE)
    first = build_history(raw, output)

    (raw / "2026-01-01" / "aaa_state_prices.html.gz").unlink()
    with gzip.open(raw / "2026-01-01" / "aaa_state_prices.html.gz", "wb") as replacement:
        replacement.write(DAY_TWO)
    second = build_history(raw, output)

    assert len(first) == len(second) == 2
    assert second[0]["regular_usd_per_gallon"] == "3.1500"
    assert output.read_text(encoding="utf-8").count("2026-01-01") == 2

