from tracker.moves import appeared_and_disappeared, calculate_moves


def row(item_id, item, regular, diesel):
    return {
        "item_id": item_id,
        "item": item,
        "regular_usd_per_gallon": str(regular),
        "midgrade_usd_per_gallon": "4.0000",
        "premium_usd_per_gallon": "4.5000",
        "diesel_usd_per_gallon": str(diesel),
    }


def test_move_rule_uses_largest_absolute_percentage_change():
    previous = [row("AL", "Alabama", 3.0, 4.0), row("TX", "Texas", 3.0, 4.0)]
    current = [row("AL", "Alabama", 3.0, 4.36), row("TX", "Texas", 3.3, 4.0)]

    moves = calculate_moves(previous, current)

    assert [move["item_id"] for move in moves] == ["TX", "AL"]
    assert moves[0]["column"] == "regular_usd_per_gallon"
    assert round(moves[0]["score"], 2) == 10.0


def test_appeared_and_disappeared_items_are_reported():
    previous = [row("AL", "Alabama", 3.0, 4.0), row("TX", "Texas", 3.0, 4.0)]
    current = [row("AL", "Alabama", 3.0, 4.0), row("CA", "California", 5.0, 6.0)]

    assert appeared_and_disappeared(previous, current) == (["CA"], ["TX"])

