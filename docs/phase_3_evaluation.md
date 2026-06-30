# Phase 3: LLM Evaluation Framework

## Goal

Add a DeepEval-powered evaluation harness that tests whether the AI Agent reasons correctly across its data engineering decisions. The harness runs as part of CI on every pull request and fails the build if the agent's quality drops below a configurable threshold.

---

## Prerequisites

- Phase 1 and Phase 2 complete.
- Add to `pyproject.toml` dependencies:
  - `deepeval>=1.0`
  - `groq>=0.5`
  - `pytest>=8.0`

Run `uv sync` after updating dependencies.

---

## What is Being Evaluated

The evaluation does not test raw data output. It tests the **agent's reasoning and decisions**:

| Evaluation target | Example question |
| --- | --- |
| Issue identification | Did the agent correctly detect a high null rate? |
| Fix appropriateness | Did the agent choose the right fix strategy for the data type? |
| Escalation accuracy | Did the agent escalate issues that required human approval? |
| Report faithfulness | Does the quality report accurately describe what happened? |
| Hallucination detection | Did the agent invent statistics not present in the data? |

---

## File Structure to Create

```text
llm_eval_pipeline/
├── evals/
│   ├── __init__.py
│   ├── test_cases.json          # 10 structured test cases
│   ├── test_agent_quality.py    # pytest file using DeepEval assertions
│   ├── scorer.py                # Applies metrics, writes reports/latest_scores.json
│   └── reporter.py              # Generates reports/report_{timestamp}.md
├── reports/                     # Output directory (git-ignored)
├── config.py                    # Add eval thresholds here (Phase 1 config extended)
└── .github/
    └── workflows/
        └── eval_ci.yml
```

---

## Tasks

### T3.1 — Extend `config.py`

Add evaluation configuration constants:

- `EVAL_THRESHOLD: float = 0.75` — minimum aggregate score to pass CI
- `EVAL_MODEL: str = "llama3-8b-8192"` — Groq model used as the evaluator
- `SCORES_OUTPUT_PATH: str = "reports/latest_scores.json"`
- `GROQ_API_KEY_ENV_VAR: str = "GROQ_API_KEY"`

### T3.2 — `evals/test_cases.json`

Create 10 test cases. Each must follow this schema:

```json
{
  "id": "tc_001",
  "description": "Human-readable label for this test case",
  "input": "The prompt or scenario given to the agent",
  "context": ["Relevant facts or data snippets the agent has access to"],
  "expected_output_criteria": ["criterion 1", "criterion 2"],
  "minimum_score": 0.75,
  "failure_mode": "hallucination | off_topic | missing_information | incorrect_format | overly_verbose"
}
```

Cover all five failure modes across the 10 cases. Suggested scenarios:

- tc_001: Agent asked to summarise a quality report with no issues — should not invent problems (hallucination)
- tc_002: Agent asked about flight delay trends — should stay on the data engineering domain (off_topic)
- tc_003: Agent asked to explain a high null rate — must mention affected column and row count (missing_information)
- tc_004: Agent asked to output a fix plan as a JSON list — must return valid JSON (incorrect_format)
- tc_005: Agent asked for a one-sentence status summary — must not write a paragraph (overly_verbose)
- tc_006–tc_010: Additional domain-specific scenarios relevant to the flight delay pipeline

### T3.3 — `evals/scorer.py`

- Function: `score_test_case(tc: dict, agent_output: str) -> dict`
  - Runs three DeepEval metrics against a single test case:
    - `AnswerRelevancyMetric(threshold=config.EVAL_THRESHOLD)`
    - `FaithfulnessMetric(threshold=config.EVAL_THRESHOLD)`
    - `HallucinationMetric(threshold=config.EVAL_THRESHOLD)`
  - Returns a dict with per-metric scores and a `passed: bool`

- Function: `score_all(test_cases: list[dict], agent_outputs: list[str]) -> dict`
  - Calls `score_test_case` for each pair
  - Computes `aggregate_score` as the mean of all per-metric scores
  - Writes result to `config.SCORES_OUTPUT_PATH`
  - Returns the full results dict

### T3.4 — `evals/reporter.py`

- Function: `generate_eval_report(scores: dict) -> str`
  - Writes a Markdown file to `reports/report_{timestamp}.md`
  - Report must include:
    - Run timestamp
    - Aggregate score vs threshold (pass/fail)
    - Per-test-case table: id, failure_mode, score, passed
    - Section listing which specific tests failed and why
  - Returns the output file path

### T3.5 — `evals/test_agent_quality.py`

- Load test cases from `evals/test_cases.json`
- For each test case, call the agent (or a mock agent function) to get `agent_output`
- Use `assert_test` from DeepEval to evaluate each output
- Each pytest test must be individually named so failures show which case failed, not just a count
- Read threshold from `config.EVAL_THRESHOLD` — do not hardcode
- After all tests, call `score_all()` and `generate_eval_report()`

### T3.6 — `.github/workflows/eval_ci.yml`

Create a GitHub Actions workflow that:

1. Triggers on every pull request to `main`
2. Sets up Python 3.11
3. Installs dependencies with `uv sync`
4. Runs `pytest evals/test_agent_quality.py -v` with `GROQ_API_KEY` from GitHub secrets
5. Fails the workflow if aggregate score in `reports/latest_scores.json` is below `config.EVAL_THRESHOLD`
6. Uploads `reports/` as a workflow artifact so scores are visible per PR

### T3.7 — Unit Tests for Scorer

Add `tests/test_scorer.py`:

- Test that `score_test_case` returns expected keys in output dict
- Test that `score_all` correctly computes aggregate as mean of per-case scores
- Test that `score_all` writes a valid JSON file to the configured output path
- Use mocked DeepEval metrics — do not make live API calls in unit tests

---

## Acceptance Criteria

- `uv run pytest evals/test_agent_quality.py -v` runs all 10 evaluation test cases
- pytest output names each failing case individually with a reason
- `reports/latest_scores.json` is written after every run with per-test and aggregate scores
- `reports/report_{timestamp}.md` is generated after every run
- GitHub Actions workflow runs on pull requests and fails if aggregate score < 0.75
- Threshold is read from `config.py` in all files — never hardcoded in test files
