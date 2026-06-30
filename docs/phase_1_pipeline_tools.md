# Phase 1: Pipeline Tools

## Goal
Build standalone, testable Python functions for every data engineering stage of the flight delay pipeline.
No agent, no LLM, no orchestration. Each module must be independently runnable and importable.

---

## Context
A Senior Data Engineer processes raw flight records through four stages:
1. Ingest raw data from a source file
2. Transform and clean the records
3. Aggregate by route and airline
4. Validate output quality and generate a quality report

The output of Phase 1 is a fully working pipeline that can be run end-to-end from the command line and produces a `data_quality_report.json`.

---

## File Structure to Create

```
llm_eval_pipeline/
├── data/
│   └── flights_raw.csv          # Static committed fixture — do NOT generate at runtime
├── pipeline/
│   ├── __init__.py
│   ├── ingestor.py              # Read raw data
│   ├── transformer.py           # Clean and enrich
│   ├── aggregator.py            # Group and summarise
│   ├── validator.py             # Quality checks
│   └── reporter.py              # Write data_quality_report.json
├── scripts/
│   └── generate_fixtures.py     # Run once by AI Agent to produce data/ and tests/fixtures/ CSVs
├── reports/                     # Output directory (git-ignored)
├── config.py                    # All thresholds, paths, column names
├── run_pipeline.py              # CLI entry point: runs all stages end-to-end
└── tests/
    ├── fixtures/
    │   ├── flights_clean.csv    # Minimal rows — passes all checks
    │   ├── flights_broken.csv   # One row per failure mode — triggers every validator check
    │   └── flights_empty.csv    # Zero data rows — triggers row_count_check
    ├── test_ingestor.py
    ├── test_transformer.py
    ├── test_aggregator.py
    └── test_validator.py
```

---

## Tasks

### T1.1 — Static raw data fixture (`data/flights_raw.csv`)
- This file is a **static committed fixture**. It must not be generated at runtime by the pipeline.
- An AI Agent must generate this file **once as a setup step** by running a dedicated script: `scripts/generate_fixtures.py`. After generation the file is committed and never regenerated automatically.
- `scripts/generate_fixtures.py` must also generate the three test fixture files under `tests/fixtures/` in the same run.
- Create a CSV with at least 200 rows of synthetic flight records.
- Columns: `flight_id`, `airline`, `origin`, `destination`, `scheduled_departure`, `actual_departure`, `status`
- The file must deliberately include the following to support TDD completeness:
  - 10–15% null values in `actual_departure` on non-`CANCELLED` rows
  - At least 5 rows where `actual_departure` is null **and** `status` is not `CANCELLED`
  - 3–5 rows with an invalid `status` value (e.g. `"UNKNWN"`)
  - 2–3 rows that are fully duplicate across all six columns: `flight_id`, `airline`, `origin`, `destination`, `scheduled_departure`, `actual_departure`
  - At least 2 rows where `delay_minutes` would exceed `config.MAX_DELAY_MINUTES` after transformation
  - At least 5 rows with leading/trailing whitespace in string columns
- Valid `status` values: `ON_TIME`, `DELAYED`, `CANCELLED`

**Test fixture rules** — each test module must use its own minimal fixture from `tests/fixtures/`, not `data/flights_raw.csv`. Test fixtures must be small (5–20 rows), deterministic, and contain exactly the rows needed to exercise the behavior under test. Never share fixtures across test modules.

### T1.2 — `config.py`
- Define the following as typed constants:
  - `RAW_DATA_PATH: str`
  - `OUTPUT_PATH: str`
  - `REPORTS_DIR: str`
  - `VALID_STATUSES: list[str]`
  - `ROUTE_COLUMN: str = "route"` — the name of the computed route column (format: `"ORIGIN-DESTINATION"`)
  - `MAX_NULL_RATE: float = 0.10`
  - `MAX_DELAY_MINUTES: int = 600`
  - `MIN_ROW_COUNT: int = 50`

### T1.3 — `pipeline/ingestor.py`
- Function: `ingest(path: str) -> pd.DataFrame`
- Reads the CSV at `path`
- Raises `FileNotFoundError` if the file does not exist
- Returns the raw DataFrame with no modifications
- Logs row count and column names on load

### T1.4 — `pipeline/transformer.py`
- Function: `transform(df: pd.DataFrame) -> pd.DataFrame`
- Steps (in order):
  1. Drop rows that are fully duplicate across all six columns: `flight_id`, `airline`, `origin`, `destination`, `scheduled_departure`, `actual_departure`. Partial matches are kept.
  2. Parse `scheduled_departure` and `actual_departure` as `datetime`
  3. Compute `delay_minutes = (actual_departure - scheduled_departure).dt.total_seconds() / 60`
  4. Set `delay_minutes = 0` for `CANCELLED` rows
  5. For rows where `actual_departure` is null **and** `status` is not `CANCELLED`: set `delay_minutes = null` (do not drop the row — the validator will flag it)
  6. Strip whitespace from string columns
  7. Standardise `status` to uppercase
  8. Add `route` column: `origin + "-" + destination` (e.g. `"LHR-FRA"`)
- Returns the enriched DataFrame

### T1.5 — `pipeline/aggregator.py`
- Function: `aggregate(df: pd.DataFrame) -> pd.DataFrame`
- Groups by `airline` and `config.ROUTE_COLUMN` (the `route` column added by transformer)
- Computes per group:
  - `avg_delay_minutes: float`
  - `total_flights: int`
  - `cancelled_rate: float` (proportion of `CANCELLED` rows)
  - `on_time_rate: float`
- Returns the aggregated DataFrame

### T1.6 — `pipeline/validator.py`
- Function: `validate(df: pd.DataFrame) -> list[dict]`
- Receives the **transformed** DataFrame (output of `transformer.transform()`)
- Runs the following checks and returns a list of issue dicts:
  - **null_rate_check**: flag columns where null rate > `config.MAX_NULL_RATE` — severity `WARNING`
  - **row_count_check**: fail if row count < `config.MIN_ROW_COUNT` — severity `CRITICAL`
  - **status_check**: flag rows where `status` not in `config.VALID_STATUSES` — severity `WARNING`
  - **delay_range_check**: flag rows where `delay_minutes` > `config.MAX_DELAY_MINUTES` — severity `WARNING`
- Each issue dict must include:
  - `check_name: str`
  - `severity: str` — `"WARNING"` or `"CRITICAL"`
  - `detail: str` — human-readable description of what was found
  - `affected_rows: int` — count of rows affected by this issue
- Returns an empty list when all checks pass

### T1.7 — `pipeline/reporter.py`
- Function: `generate_report(issues: list[dict], df: pd.DataFrame, output_path: str) -> str`
- Writes `data_quality_report.json` to `output_path`
- Returns `output_path` as a string so callers (e.g. `run_pipeline.py`) can print or log it
- `total_rows` is the row count of `df` **after transformation** (duplicates already dropped)
- Report structure:
  ```json
  {
    "run_timestamp": "<ISO 8601>",
    "total_rows": 0,
    "issues_found": 0,
    "critical_count": 0,
    "warning_count": 0,
    "issues": []
  }
  ```

### T1.8 — `run_pipeline.py`
- CLI entry point that calls all stages in order: ingest → transform → aggregate → validate → report
- Prints a summary to stdout: row count, issues found, output path
- Accepts `--dry-run` flag: runs all stages **but skips all disk writes entirely** (no report file, no aggregated output). Prints the same stdout summary so behavior is still visible.

### T1.9 — Unit Tests

All tests must use fixtures from `tests/fixtures/`. Each test module uses its own fixture file. No test may import or read `data/flights_raw.csv`.

**`tests/test_ingestor.py`** — uses `flights_clean.csv`
- Assert returned DataFrame has the expected 7 columns
- Assert row count matches the fixture row count exactly
- Assert `FileNotFoundError` is raised when path does not exist
- Assert empty CSV (header only) returns a DataFrame with zero rows and correct columns

**`tests/test_transformer.py`** — uses a programmatically constructed DataFrame (no fixture file needed)
- Assert `delay_minutes` is computed correctly for a `DELAYED` row with known timestamps
- Assert `delay_minutes = 0` for a `CANCELLED` row
- Assert `delay_minutes` is null for a non-`CANCELLED` row where `actual_departure` is null
- Assert fully duplicate rows (all six key columns identical) are dropped; non-duplicate rows are kept
- Assert `route` column is added in format `"ORIGIN-DESTINATION"`
- Assert whitespace is stripped from string columns
- Assert `status` is uppercased

**`tests/test_aggregator.py`** — uses a programmatically constructed DataFrame
- Assert output contains columns: `airline`, `route`, `avg_delay_minutes`, `total_flights`, `cancelled_rate`, `on_time_rate`
- Assert `total_flights` matches the input row count for a single-group input
- Assert `cancelled_rate` is 1.0 when all rows in a group are `CANCELLED`
- Assert single-row DataFrame produces a valid one-row aggregated output

**`tests/test_validator.py`** — uses `flights_broken.csv` and `flights_clean.csv`
- Assert `null_rate_check` fires when a column exceeds `config.MAX_NULL_RATE`; `affected_rows` equals the null count
- Assert `row_count_check` fires with `severity = "CRITICAL"` when row count < `config.MIN_ROW_COUNT`; use `flights_empty.csv`
- Assert `status_check` fires for each invalid status row
- Assert `delay_range_check` fires when `delay_minutes` exceeds `config.MAX_DELAY_MINUTES`
- Assert **empty list is returned** when `flights_clean.csv` passes through transform then validate
- Assert each issue dict contains all four required keys: `check_name`, `severity`, `detail`, `affected_rows`

---

## Acceptance Criteria
- `uv run python run_pipeline.py` completes without error and prints a summary
- `reports/data_quality_report.json` is created with correct structure
- `uv run pytest tests/` passes with no failures
- No hardcoded paths outside `config.py`
