# American Gas Tracker

[![Tests](https://github.com/OWNER/REPOSITORY/actions/workflows/tests.yml/badge.svg)](https://github.com/OWNER/REPOSITORY/actions/workflows/tests.yml)

American Gas Tracker is a daily data tracker for the Financial Data Analytics Data Tracker Project. It records AAA's average gasoline and diesel prices for all 50 U.S. states and Washington, D.C., rebuilds a reproducible history, opens a daily GitHub Issue, and publishes a browser-based GitHub Pages site.

## Source and scope

The project has one source:

| Source | Format | URL | Items kept | Numeric values |
|---|---|---|---|---|
| `aaa_state_prices` | HTML | <https://gasprices.aaa.com/state-gas-price-averages/> | All 50 states plus Washington, D.C. | Regular, mid-grade, premium, and diesel U.S. dollars per gallon |

AAA states that its Fuel Prices website is updated daily around 3 a.m. Eastern by OPIS. The pipeline runs at 09:15 UTC, after that expected refresh window. The page is public and does not require an API key or login. The parser keeps exactly the 51 state/DC rows from the state table; it does not collect the larger county or metro pages.

The repository must remain non-commercial and must attribute AAA as the source. AAA's [site terms](https://gasprices.aaa.com/about-aaa/) should be reviewed with the instructor before publishing daily raw snapshots in a public repository. If permission is not acceptable, replace this source before the first graded run with an explicitly redistributable U.S. source and update `tracker/sources.py`, the tests, and this README.

## History data

`data/history.csv` has one row per item per successful source date. Dates are UTC dates in `YYYY-MM-DD` format. The first four columns are the required fixed columns.

| Column | Meaning | Unit |
|---|---|---|
| `date` | UTC date of the source snapshot | `YYYY-MM-DD` |
| `item_id` | Stable state key, such as `TX` | — |
| `item` | State or District of Columbia name | — |
| `source` | Source identifier | — |
| `region` | U.S. Census-style project grouping: Northeast, Midwest, South, or West | — |
| `regular_usd_per_gallon` | Average regular gasoline price | USD/gallon |
| `midgrade_usd_per_gallon` | Average mid-grade gasoline price | USD/gallon |
| `premium_usd_per_gallon` | Average premium gasoline price | USD/gallon |
| `diesel_usd_per_gallon` | Average diesel price | USD/gallon |

The movement score is the largest absolute percentage change across the four numeric price columns for an item:

```text
score = max(abs((new_value - old_value) / old_value) * 100)
```

If the old value is zero, the absolute dollar difference is used. The daily Issue lists the ten items with the largest scores, including old value, new value, difference, and field. It also lists appeared and disappeared item IDs. An Issue is opened even when there are no changes; a rerun on the same day updates that day's Issue and closes older tracker Issues.

Build the history from raw files with:

```bash
python -m tracker.history --raw-dir data/raw --output data/history.csv
```

The history builder reads only `data/raw/<date>/aaa_state_prices.html.gz` files, so changing a parsing rule and rerunning the command rebuilds every historical day deterministically.

## Pipeline behavior

Run a normal snapshot locally with:

```bash
python pipeline.py
```

To rebuild without downloading:

```bash
python pipeline.py --skip-fetch
```

Each run:

1. Downloads the AAA HTML page and saves it as `data/raw/<UTC-date>/aaa_state_prices.html.gz`.
2. Validates that at least ten states and all four price fields were parsed. A failed or incomplete source writes no raw source file for that date.
3. Records every source result, including failures, in `data/raw/<UTC-date>/source_results.json`.
4. Rebuilds `data/history.csv` from all raw files.
5. Writes `data/status.json`.
6. Builds the daily Issue body in `data/issue.md` and publishes or updates the Issue when GitHub credentials are available.
7. The GitHub Actions workflow commits raw files, history, status, and the Issue body.

`data/status.json` contains `run_time`, `first_run_date`, `days_with_success`, `items`, `new_today`, `gone_today`, and one `{name, ok, count}` entry per source.

## Website

The Pages site has three pages:

- `index.html` is the Today page. It loads `data/history.csv` and `data/status.json`, shows the last run, source status, counts, latest state values, regular-price changes, and biggest moves.
- `browse.html` is the Browse page. It filters by region and source, searches state names, sorts every numeric column in both directions, and stores shortlist stars in browser `localStorage`.
- `trends.html` is the Trends page. It has an item/metric picker and four findings calculated in the browser from `history.csv`: regular-price spread, premium markup, diesel gap, and average regular price since the first run. Each finding includes a written calculation and chart.

The site includes `manifest.webmanifest`, `icon.svg`, and `sw.js`. The service worker caches the app shell and uses network-first loading for the two data files, so online visits receive new data and offline visits retain the last loaded snapshot.

## Tests and Actions

Run tests locally:

```bash
python -m pip install -r requirements.txt
python -m pytest
```

The tests cover AAA HTML conversion, source validation, deterministic history rebuilding, replacement of a same-day raw file, the movement rule, and appeared/disappeared items. `.github/workflows/tests.yml` runs pytest on every push and pull request.

`.github/workflows/daily.yml` runs the pipeline once per day, has `contents: write` and `issues: write` permissions, publishes the daily Issue, and commits the data. `.github/workflows/pages.yml` assembles the site with the two fixed data files and deploys it to GitHub Pages. In the repository settings, choose GitHub Actions as the Pages build source if GitHub has not enabled it automatically.

## File guide

| File | Purpose |
|---|---|
| `.github/workflows/tests.yml` | Runs pytest on pushes and pull requests. |
| `.github/workflows/daily.yml` | Daily fetch, Issue, data commit, and manual dispatch workflow. |
| `.github/workflows/pages.yml` | Builds and deploys the installable Pages site. |
| `pipeline.py` | Daily orchestration entry point. |
| `tracker/config.py` | Source metadata, numeric columns, and all 51 tracked items. |
| `tracker/sources.py` | AAA fetch, HTML table parser, and source validation. |
| `tracker/history.py` | Raw-file-only history builder and CLI. |
| `tracker/moves.py` | Shared move and appeared/disappeared calculations. |
| `tracker/issues.py` | Issue body generation and GitHub Issue API integration. |
| `tracker/__init__.py` | Python package marker and package description. |
| `data/history.csv` | Fixed-path historical output. |
| `data/status.json` | Fixed-path latest-run status output. |
| `data/raw/` | Compressed daily source snapshots and source result records. |
| `data/issue.md` | Generated body of the latest daily Issue. |
| `site/index.html` | Today page. |
| `site/browse.html` | Browse/filter/shortlist page. |
| `site/trends.html` | Browser-computed trends page. |
| `site/app.js` | Shared data loading, navigation, calculations, and SVG charts. |
| `site/today.js` | Today page rendering. |
| `site/browse.js` | Browse filters, sorting, and shortlist behavior. |
| `site/trends.js` | Trend calculations, findings, and charts. |
| `site/styles.css` | Shared fonts, colors, layout, and responsive styling. |
| `site/manifest.webmanifest` | Installable web app manifest. |
| `site/sw.js` | Offline cache and network-first data service worker. |
| `site/icon.svg` | App icon. |
| `tests/test_sources.py` | Source conversion and validation tests. |
| `tests/test_history.py` | History ordering and same-day replacement tests. |
| `tests/test_moves.py` | Movement and item appearance tests. |
| `requirements.txt` | Pytest dependency. |
| `pyproject.toml` | Pytest configuration. |
| `.gitignore` | Local Python/build exclusions. |

## Submission checklist

Before submitting, make the repository public, enable GitHub Pages, confirm the Tests badge is passing, confirm the first daily run succeeded, and allow the workflow to complete successfully on at least seven different UTC dates. The final text file should contain the required name, student ID, public repository URL, and live site URL.

