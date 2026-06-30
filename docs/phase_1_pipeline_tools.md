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
│   └── flights_raw.csv          # Sample raw data (generated or static fixture)
├── pipeline/
│   ├── __init__.py
│   ├── ingestor.py              # Read raw data
│   ├── transformer.py           # Clean and enrich
│   ├── aggregator.py            # Group and summarise
│   ├── validator.py             # Quality checks
│   └── reporter.py              # Write data_quality_report.json
├── reports/                     # Output directory (git-ignored)
├── config.py                    # All thresholds, paths, column names
├── run_pipeline.py              # CLI entry point: runs all stages end-to-end
└── tests/
    ├── test_ingestor.py
    ├── test_transformer.py
    ├── test_aggregator.py
    └── test_validator.py
```

---

## Tasks

### T1.1 — Generate sample raw data (`data/flights_raw.csv`)
- Create a CSV with at least 200 rows of synthetic flight records.
- Columns: `flight_id`, `airline`, `origin`, `destination`, `scheduled_departure`, `actual_departure`, `status`
- Intentionally include:
  - 10–15% null values in `actual_departure`
  - 3–5 rows with an invalid `status` value (e.g. `"UNKNWN"`)
  - 2–3 duplicate `flight_id` rows
- Valid `status` values: `ON_TIME`, `DELAYED`, `CANCELLED`

### T1.2 — `config.py`
- Define the following as typed constants:
  - `RAW_DATA_PATH: str`
  - `OUTPUT_PATH: str`
  - `REPORTS_DIR: str`
  - `VALID_STATUSES: list[str]`
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
  1. Drop fully duplicate rows (same `flight_id`)
  2. Parse `scheduled_departure` and `actual_departure` as `datetime`
  3. Compute `delay_minutes = (actual_departure - scheduled_departure).dt.total_seconds() / 60`
  4. Set `delay_minutes = 0` for `CANCELLED` rows
  5. Strip whitespace from string columns
  6. Standardise `status` to uppercase
- Returns the enriched DataFrame

### T1.5 — `pipeline/aggregator.py`
- Function: `aggregate(df: pd.DataFrame) -> pd.DataFrame`
- Groups by `airline` and `origin`→`destination` route
- Computes per group:
  - `avg_delay_minutes: float`
  - `total_flights: int`
  - `cancelled_rate: float` (proportion of `CANCELLED` rows)
  - `on_time_rate: float`
- Returns the aggregated DataFrame

### T1.6 — `pipeline/validator.py`
- Function: `validate(df: pd.DataFrame) -> list[dict]`
- Runs the following checks and returns a list of issue dicts:
  - **null_rate_check**: flag columns where null rate > `config.MAX_NULL_RATE`
  - **row_count_check**: fail if row count < `config.MIN_ROW_COUNT`
  - **status_check**: flag rows where `status` not in `config.VALID_STATUSES`
  - **delay_range_check**: flag rows where `delay_minutes` > `config.MAX_DELAY_MINUTES`
- Each issue dict must include: `check_name`, `severity` (`WARNING` | `CRITICAL`), `detail`, `affected_rows`

### T1.7 — `pipeline/reporter.py`
- Function: `generate_report(issues: list[dict], df: pd.DataFrame, output_path: str) -> None`
- Writes `data_quality_report.json` to `output_path`
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
- Accepts `--dry-run` flag: runs all stages but does not write to disk

### T1.9 — Unit Tests
- `tests/test_ingestor.py`: assert correct row count and column names from fixture CSV
- `tests/test_transformer.py`: assert `delay_minutes` is computed correctly; assert duplicates are removed
- `tests/test_aggregator.py`: assert aggregated output has expected columns and no null keys
- `tests/test_validator.py`: assert each check fires correctly on a deliberately broken fixture

---

## Acceptance Criteria
- `uv run python run_pipeline.py` completes without error and prints a summary
- `reports/data_quality_report.json` is created with correct structure
- `uv run pytest tests/` passes with no failures
- No hardcoded paths outside `config.py`
