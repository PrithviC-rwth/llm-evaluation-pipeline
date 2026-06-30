# BLUEPRINT: LLM Evaluation Pipeline with Automated Regression Testing

## YOUR ROLE
You are a senior AI/ML engineer building a production-grade LLM evaluation and regression testing system. Generate complete, runnable code with clean architecture and thorough inline documentation.

## PROJECT OVERVIEW
Build an evaluation pipeline that:

1. Defines test cases with inputs, expected behavior, and quality criteria
2. Runs each test case through a target LLM (Groq/Llama3)
3. Scores outputs using DeepEval metrics (relevancy, faithfulness, answer correctness)
4. Generates a test report
5. Fails CI if average score drops below a configurable threshold

## TECH STACK
- DeepEval for evaluation metrics
- pytest as the test runner
- Groq API (llama3–8b-8192) - use GROQ_API_KEY environment variable
- GitHub Actions for CI/CD
- Python 3.10+

## FILE STRUCTURE TO GENERATE
llm_eval_pipeline/
├── evals/
│ ├── test_cases.json # 10 sample test cases covering different failure modes
│ └── test_llm_quality.py # pytest file using DeepEval assertions
├── pipeline/
│ ├── runner.py # Runs LLM against test cases, returns raw outputs
│ ├── scorer.py # Applies DeepEval metrics, returns structured scores
│ └── reporter.py # Generates markdown report of results
├── config.py # Thresholds, model config, environment variables
├── .github/
│ └── workflows/
│ └── eval_ci.yml # GitHub Actions workflow: run evals on every PR
├── requirements.txt
└── README.md

## TEST CASE REQUIREMENTS
- Include at least 10 test cases in test_cases.json
- Cover these failure modes: hallucination, off-topic response, missing key information, incorrect format, overly verbose output
- Each test case must include: input, context (if RAG), expected_output_criteria (list of strings), minimum_score (float 0–1)

## EXPLICIT REQUIREMENTS
- DeepEval metrics to use: AnswerRelevancyMetric, FaithfulnessMetric, HallucinationMetric
- Scorer must output per-test scores AND aggregate score to a JSON file: reports/latest_scores.json
- GitHub Actions workflow must: install dependencies, run pytest, fail if aggregate score < threshold in config.py
- Threshold must be configurable - default 0.75
- Reporter must generate reports/report_{timestamp}.md after every run

## CONSTRAINTS
- Do not use OpenAI - Groq only
- Do not hardcode thresholds in test files - read from config.py
- pytest output must show which specific tests failed and why, not just a pass/fail count
- Add a - dry-run flag to runner.py that prints test cases without calling the API

## PERSONALIZATION NOTE FOR THE BUILDER
This foundation gives you a working eval pipeline. Here's where you take it further:
- Add your own domain-specific test cases (customer support, code generation, summarization)
- Create a Streamlit dashboard that visualizes score trends across runs
- Add a Slack notification when CI fails
- Experiment with different evaluator models and compare their judgment consistency
- Write a blog post about what you learned - "I built an AI test suite and here's what broke"