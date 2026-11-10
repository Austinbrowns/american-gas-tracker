"""Fetching and parsing for the project's one live source."""

from __future__ import annotations

from html.parser import HTMLParser
import re
from typing import Any
from urllib.request import Request, urlopen

from .config import NUMERIC_COLUMNS, SOURCE_URL, STATE_BY_NAME


class _TableParser(HTMLParser):
    """Collect table rows without requiring a third-party HTML dependency."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "tr":
            self._row = []
        elif tag in {"th", "td"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"th", "td"} and self._cell is not None and self._row is not None:
            self._row.append("".join(self._cell))
            self._cell = None
        elif tag == "tr" and self._row:
            self.rows.append(self._row)
            self._row = None


def _clean(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def _header_key(value: str) -> str:
    return re.sub(r"[^a-z]", "", _clean(value).casefold())


def _price(value: str) -> float | None:
    match = re.search(r"\d+(?:,\d{3})*(?:\.\d+)?", value)
    return float(match.group(0).replace(",", "")) if match else None


def parse_aaa_html(html: bytes | str) -> list[dict[str, Any]]:
    """Convert the AAA state table into the project's common row shape."""

    text = html.decode("utf-8", errors="replace") if isinstance(html, bytes) else html
    parser = _TableParser()
    parser.feed(text)

    header_index: dict[str, int] | None = None
    for row in parser.rows:
        normalized = [_header_key(cell) for cell in row]
        if {"state", "regular", "midgrade", "premium", "diesel"}.issubset(normalized):
            header_index = {name: normalized.index(name) for name in ("state", "regular", "midgrade", "premium", "diesel")}
            break
    if header_index is None:
        raise ValueError("AAA state table header was not found")

    records: list[dict[str, Any]] = []
    for row in parser.rows:
        if len(row) <= max(header_index.values()):
            continue
        state_name = _clean(row[header_index["state"]])
        state = STATE_BY_NAME.get(state_name.casefold())
        if state is None:
            continue
        values = {
            "regular_usd_per_gallon": _price(row[header_index["regular"]]),
            "midgrade_usd_per_gallon": _price(row[header_index["midgrade"]]),
            "premium_usd_per_gallon": _price(row[header_index["premium"]]),
            "diesel_usd_per_gallon": _price(row[header_index["diesel"]]),
        }
        records.append({**state, **values})

    unique = {record["item_id"]: record for record in records}
    return [unique[item_id] for item_id in sorted(unique)]


def fetch_aaa_html(url: str = SOURCE_URL, timeout: int = 30) -> bytes:
    """Download the public AAA HTML page."""

    request = Request(
        url,
        headers={
            "User-Agent": "gas-price-tracker/1.0 (educational project; contact repository owner)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        body = response.read()
        if not body:
            raise ValueError("AAA returned an empty response")
        return body


def validate_source_records(records: list[dict[str, Any]]) -> None:
    """Fail closed if the source layout changes or the page is incomplete."""

    if len(records) < 10:
        raise ValueError(f"AAA returned only {len(records)} recognizable states; refusing to save it")
    for record in records:
        missing = [column for column in NUMERIC_COLUMNS if record.get(column) is None]
        if missing:
            raise ValueError(f"Missing numeric values for {record['item_id']}: {', '.join(missing)}")

