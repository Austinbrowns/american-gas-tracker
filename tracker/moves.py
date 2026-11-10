"""Deterministic movement calculations shared by the pipeline and tests."""

from __future__ import annotations

from typing import Any

from .config import NUMERIC_COLUMNS


def _number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def calculate_moves(previous: list[dict[str, Any]], current: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return common items sorted by largest absolute percentage movement."""

    old_by_id = {row["item_id"]: row for row in previous}
    moves: list[dict[str, Any]] = []
    for row in current:
        old = old_by_id.get(row["item_id"])
        if old is None:
            continue
        changes: list[dict[str, Any]] = []
        for column in NUMERIC_COLUMNS:
            before = _number(old.get(column))
            after = _number(row.get(column))
            if before is None or after is None:
                continue
            difference = after - before
            score = abs(difference / before) * 100 if before else abs(difference)
            changes.append({"column": column, "old": before, "new": after, "difference": difference, "score": score})
        if not changes:
            continue
        biggest = max(changes, key=lambda change: (change["score"], change["column"]))
        moves.append(
            {
                "item_id": row["item_id"],
                "item": row["item"],
                "score": biggest["score"],
                "column": biggest["column"],
                "old": biggest["old"],
                "new": biggest["new"],
                "difference": biggest["difference"],
            }
        )
    return sorted(moves, key=lambda move: (-move["score"], move["item_id"]))


def appeared_and_disappeared(previous: list[dict[str, Any]], current: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    old_ids = {row["item_id"] for row in previous}
    new_ids = {row["item_id"] for row in current}
    return sorted(new_ids - old_ids), sorted(old_ids - new_ids)

