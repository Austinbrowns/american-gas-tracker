from tracker.sources import parse_aaa_html, validate_source_records


SAMPLE = b"""
<html><body>
<table><tr><th>State</th><th>Regular</th><th>Mid-Grade</th><th>Premium</th><th>Diesel</th></tr>
<tr><td>Alabama</td><td>$3.1000</td><td>$3.5000</td><td>$3.9000</td><td>$4.2000</td></tr>
<tr><td>Texas</td><td>$3.2000</td><td>$3.6000</td><td>$4.0000</td><td>$4.3000</td></tr>
</table>
</body></html>
"""


def test_aaa_table_converts_to_common_rows():
    rows = parse_aaa_html(SAMPLE)
    assert [row["item_id"] for row in rows] == ["AL", "TX"]
    assert rows[0]["item"] == "Alabama"
    assert rows[0]["region"] == "South"
    assert rows[0]["regular_usd_per_gallon"] == 3.1
    assert rows[1]["diesel_usd_per_gallon"] == 4.3


def test_source_validator_rejects_incomplete_item_set():
    rows = parse_aaa_html(SAMPLE)
    try:
        validate_source_records(rows)
    except ValueError as exc:
        assert "only 2" in str(exc)
    else:
        raise AssertionError("incomplete source should be rejected")

