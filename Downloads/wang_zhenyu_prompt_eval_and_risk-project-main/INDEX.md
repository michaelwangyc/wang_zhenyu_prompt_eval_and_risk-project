# Project Source Code Index

## `prompt_risk/` — Python Package

Core library for prompt risk evaluation. Loads versioned prompt templates from data files, invokes LLM via AWS Bedrock, parses structured output, and evaluates results against data-driven assertions.

### Top-level modules

- [prompts.py](prompt_risk/prompts.py) — `Prompt` dataclass: resolves versioned prompt templates (Jinja2) from the `data/` directory and renders them with runtime data.
- [evaluations.py](prompt_risk/evaluations.py) — Generic, model-agnostic evaluation engine. Compares LLM output against assertions defined in test-case TOML files. Supports three assertion types: `expected` (ground-truth match), `attack_target` (injection detection via `!=`).
- [bedrock_utils.py](prompt_risk/bedrock_utils.py) — Thin wrapper around the AWS Bedrock Converse API. Sends system/user messages and returns the assistant's text response.
- [llm_output.py](prompt_risk/llm_output.py) — Post-processing utilities for raw LLM text responses (e.g. JSON extraction from fenced code blocks).
- [constants.py](prompt_risk/constants.py) — Enumerations for use-case IDs (`UseCaseIdEnum`) and prompt IDs (`PromptIdEnum`). Each prompt ID encodes its use case and short name (e.g. `uc1-claim-intake:p1-extraction`).
- [paths.py](prompt_risk/paths.py) — `PathEnum` singleton providing absolute paths to all project directories and files (source, tests, data, docs, build artifacts).
- [exc.py](prompt_risk/exc.py) — Custom exceptions (`JsonExtractionError`).

### `prompt_risk/judges/` — Judge modules

LLM-as-judge implementations. Each judge evaluates a target prompt for a specific risk category.

- [j1_over_permissive.py](prompt_risk/judges/j1_over_permissive.py) — J1 Over-Permissive Authorization Judge. Use-case-agnostic: accepts raw prompt text and returns a structured `J1Result` with per-criterion findings and an overall risk score.

### `prompt_risk/uc/` — Use-case runners

Use-case-specific modules that wire together prompts, test data loaders, and runners.

- [uc/uc1/](prompt_risk/uc/uc1/) — UC1 Claim Intake use case:
  - [p1_extraction_runner.py](prompt_risk/uc/uc1/p1_extraction_runner.py) — Runs the P1 FNOL extraction prompt via Bedrock and parses output into `P1ExtractionOutput`.
  - [p1_test_data.py](prompt_risk/uc/uc1/p1_test_data.py) — Data loader for P1 normal and attack test cases (reads TOML files from `data/`).
  - [p2_classification_runner.py](prompt_risk/uc/uc1/p2_classification_runner.py) — Runs the P2 classification prompt.
  - [p2_test_data.py](prompt_risk/uc/uc1/p2_test_data.py) — Data loader for P2 test cases.
  - [p3_triage_runner.py](prompt_risk/uc/uc1/p3_triage_runner.py) — Runs the P3 triage prompt.
  - [p3_test_data.py](prompt_risk/uc/uc1/p3_test_data.py) — Data loader for P3 test cases.
  - [j1_uc1_p1.py](prompt_risk/uc/uc1/j1_uc1_p1.py) — Wrapper: runs J1 judge on UC1-P1 extraction prompt with concrete test data.

### `prompt_risk/one/` — Runtime environment

Singleton (`one`) that provides project configuration and AWS session/client access.

- [one_01_main.py](prompt_risk/one/one_01_main.py) — `One` class composing all mixins; exports the `one` singleton.
- [one_02_config.py](prompt_risk/one/one_02_config.py) — Configuration mixin (placeholder).
- [one_03_boto_ses.py](prompt_risk/one/one_03_boto_ses.py) — Boto3 session and Bedrock runtime client mixin.
- [api.py](prompt_risk/one/api.py) — Re-exports `one` for convenient import.

### `prompt_risk/tests/` — Test helpers

- [helper.py](prompt_risk/tests/helper.py) — Wrappers around `pytest_cov_helper` for running unit tests and coverage from `if __name__ == "__main__":` blocks.

### `prompt_risk/vendor/` — Vendored utilities

- [pytest_cov_helper.py](prompt_risk/vendor/pytest_cov_helper.py) — Helper for running pytest with coverage as a subprocess.

---

## `examples/` — Runnable Scripts

End-to-end example scripts demonstrating how to use the library. Each script pins a prompt version and test case, then runs the pipeline.

- [uc1-claim-intake/](examples/uc1-claim-intake/) — UC1 Claim Intake examples:
  - [run_uc1_p1_extraction.py](examples/uc1-claim-intake/run_uc1_p1_extraction.py) — Run P1 extraction on a selected test case and evaluate the output.
  - [run_uc1_p2_classification.py](examples/uc1-claim-intake/run_uc1_p2_classification.py) — Run P2 classification.
  - [run_uc1_p3_triage.py](examples/uc1-claim-intake/run_uc1_p3_triage.py) — Run P3 triage.
- [judges/](examples/judges/) — Judge examples:
  - [run_j1_on_uc1_p1.py](examples/judges/run_j1_on_uc1_p1.py) — Run J1 Over-Permissive judge on UC1-P1 prompt across all test data loaders.

---

## `docs/source/` — Documentation

Sphinx documentation source. Narrative docs are RST files; demo notebooks are Jupyter (`.ipynb` for humans, `.md` export for AI consumption).

- [index.rst](docs/source/index.rst) — Documentation root (table of contents, README include)

### 01-Project-Background — Research context and risk framework

- [index.rst](docs/source/01-Project-Background/index.rst) — Project Background: LLM Prompt Risk Management for the Insurance Industry
  - [01-Risk-Taxonomy/index.rst](docs/source/01-Project-Background/01-Risk-Taxonomy/index.rst) — Internal Prompt Authoring Risk: Risk Taxonomy (five risk categories: Over-Permissive Authorization, Hardcoded Sensitive Data, Role Confusion, Instruction Conflict, Logic Ambiguity)
  - [02-Prompt-Risk-Matrix/index.rst](docs/source/01-Project-Background/02-Prompt-Risk-Matrix/index.rst) — Internal Prompt Authoring Risk: Prompt Risk Matrix (three-dimensional scoring: Exploitability, Impact, Detectability)
  - [03-Governance-Recommendations/index.rst](docs/source/01-Project-Background/03-Governance-Recommendations/index.rst) — Internal Prompt Authoring Risk: Governance Recommendations (Authoring Guidelines, Four-Gate Audit Workflow, Automated Scanning, Framework Alignment)

### 02 through 08 — Design docs and demos

- [02-Use-Case-Catalog/index.rst](docs/source/02-Use-Case-Catalog/index.rst) — Use Case Catalog: AI Applications with Prompt Exposure in Insurance
- [03-Judge-Catalog/index.rst](docs/source/03-Judge-Catalog/index.rst) — Judge Catalog: LLM-as-Judge Security Evaluation Pipeline
- [04-Data-Structure-Design/index.rst](docs/source/04-Data-Structure-Design/index.rst) — Data Structure Design: Prompt & Test Data Organization
- [05-Prompt-Runner-And-Evaluation/index.rst](docs/source/05-Prompt-Runner-And-Evaluation/index.rst) — Prompt Runner & Evaluation Pipeline
- 06-Prompt-Runner-And-Evaluation-Demo — UC1-P1 Extraction: Prompt Runner & Evaluation Demo
  - [index.ipynb](docs/source/06-Prompt-Runner-And-Evaluation-Demo/index.ipynb) — Jupyter notebook (interactive)
  - [index.md](docs/source/06-Prompt-Runner-And-Evaluation-Demo/index.md) — Markdown export (AI-readable)
- [07-Judge-Design/index.rst](docs/source/07-Judge-Design/index.rst) — Judge Design: LLM-as-Judge Prompt Security Evaluation
- 08-Judge-Demo — J1 Over-Permissive Authorization Judge Demo
  - [index.ipynb](docs/source/08-Judge-Demo/index.ipynb) — Jupyter notebook (interactive)
  - [index.md](docs/source/08-Judge-Demo/index.md) — Markdown export (AI-readable)

### 99-Maintainer-Guide — Project infrastructure

- [index.rst](docs/source/99-Maintainer-Guide/index.rst) — Maintainer Guide
  - [01-Project-Overview/index.rst](docs/source/99-Maintainer-Guide/01-Project-Overview/index.rst) — Project Overview (dev tools: mise, uv, Claude Code, pytest, Sphinx, GitHub Actions)
