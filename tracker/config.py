"""Project configuration and the fixed item universe."""

SOURCE_NAME = "aaa_state_prices"
SOURCE_URL = "https://gasprices.aaa.com/state-gas-price-averages/"
SOURCE_LABEL = "AAA U.S. state averages"

NUMERIC_COLUMNS = (
    "regular_usd_per_gallon",
    "midgrade_usd_per_gallon",
    "premium_usd_per_gallon",
    "diesel_usd_per_gallon",
)

HISTORY_COLUMNS = (
    "date",
    "item_id",
    "item",
    "source",
    "region",
    *NUMERIC_COLUMNS,
)

_STATES = [
    ("AL", "Alabama", "South"),
    ("AK", "Alaska", "West"),
    ("AZ", "Arizona", "West"),
    ("AR", "Arkansas", "South"),
    ("CA", "California", "West"),
    ("CO", "Colorado", "West"),
    ("CT", "Connecticut", "Northeast"),
    ("DE", "Delaware", "Northeast"),
    ("DC", "District of Columbia", "Northeast"),
    ("FL", "Florida", "South"),
    ("GA", "Georgia", "South"),
    ("HI", "Hawaii", "West"),
    ("ID", "Idaho", "West"),
    ("IL", "Illinois", "Midwest"),
    ("IN", "Indiana", "Midwest"),
    ("IA", "Iowa", "Midwest"),
    ("KS", "Kansas", "Midwest"),
    ("KY", "Kentucky", "South"),
    ("LA", "Louisiana", "South"),
    ("ME", "Maine", "Northeast"),
    ("MD", "Maryland", "Northeast"),
    ("MA", "Massachusetts", "Northeast"),
    ("MI", "Michigan", "Midwest"),
    ("MN", "Minnesota", "Midwest"),
    ("MS", "Mississippi", "South"),
    ("MO", "Missouri", "Midwest"),
    ("MT", "Montana", "West"),
    ("NE", "Nebraska", "Midwest"),
    ("NV", "Nevada", "West"),
    ("NH", "New Hampshire", "Northeast"),
    ("NJ", "New Jersey", "Northeast"),
    ("NM", "New Mexico", "West"),
    ("NY", "New York", "Northeast"),
    ("NC", "North Carolina", "South"),
    ("ND", "North Dakota", "Midwest"),
    ("OH", "Ohio", "Midwest"),
    ("OK", "Oklahoma", "South"),
    ("OR", "Oregon", "West"),
    ("PA", "Pennsylvania", "Northeast"),
    ("RI", "Rhode Island", "Northeast"),
    ("SC", "South Carolina", "South"),
    ("SD", "South Dakota", "Midwest"),
    ("TN", "Tennessee", "South"),
    ("TX", "Texas", "South"),
    ("UT", "Utah", "West"),
    ("VT", "Vermont", "Northeast"),
    ("VA", "Virginia", "South"),
    ("WA", "Washington", "West"),
    ("WV", "West Virginia", "South"),
    ("WI", "Wisconsin", "Midwest"),
    ("WY", "Wyoming", "West"),
]

STATE_INFO = [
    {"item_id": item_id, "item": item, "region": region}
    for item_id, item, region in _STATES
]
STATE_BY_NAME = {row["item"].casefold(): row for row in STATE_INFO}
STATE_BY_ID = {row["item_id"]: row for row in STATE_INFO}

