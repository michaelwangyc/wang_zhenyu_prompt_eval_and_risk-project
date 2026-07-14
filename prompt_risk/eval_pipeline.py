# -*- coding: utf-8 -*-

"""Evaluation pipeline — run every test case against its prompt and aggregate metrics.

This module is the batch entry point for the assertion-based evaluation layer
(:mod:`prompt_risk.evaluations`).  While ``tests_manual/`` scripts run one
prompt's cases interactively, this pipeline runs **all** discovered test cases
across every registered prompt, aggregates pass/fail metrics, and emits a
machine-readable report for CI and regression tracking.

Test cases are **discovered from the filesystem**, not hand-registered: any
``*.toml`` file under a prompt's ``normal/`` or ``attack/`` directory is
picked up automatically, so adding a new test case never requires touching
Python code.

The resulting :class:`EvalReport` separates two quality dimensions:

- **normal** cases measure business correctness (``expected`` assertions);
- **attack** cases measure adversarial resistance (``attack_target``
  assertions — the output must NOT contain attacker-injected values).

Run from the command line::

    python -m prompt_risk.eval_pipeline --output tmp/eval-metrics.json

or in CI with S3 persistence and regression thresholds::

    python -m prompt_risk.eval_pipeline \\
        --output tmp/eval-metrics.json \\
        --s3-bucket my-metrics-bucket \\
        --min-normal-pass-rate 0.8 \\
        --min-attack-pass-rate 1.0
"""

import typing as T
import argparse
import dataclasses
import os
import subprocess
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

from .constants import PromptIdEnum
from .evaluations import evaluate, FieldEvalResult
from .uc.uc1.p1_extraction_runner import (
    P1ExtractionUserPromptData,
    run_p1_extraction,
)
from .uc.uc1.p2_classification_runner import (
    P2ClassificationUserPromptData,
    run_p2_classification,
)
from .uc.uc1.p3_triage_runner import (
    P3TriageUserPromptData,
    run_p3_triage,
)

if T.TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime import BedrockRuntimeClient

DEFAULT_MODEL_ID = "us.amazon.nova-2-lite-v1:0"

T_CASE_TYPE = T.Literal["normal", "attack"]


# ------------------------------------------------------------------------------
# Test case discovery
# ------------------------------------------------------------------------------
class EvalCase(BaseModel):
    """One test case loaded from a ``normal/`` or ``attack/`` TOML file."""

    prompt_id: str
    case_type: T_CASE_TYPE
    name: str
    input: dict
    expected: dict | None = None
    attack_target: dict | None = None


def discover_cases(prompt_id: PromptIdEnum) -> list[EvalCase]:
    """Discover all test-case TOML files for *prompt_id* from the data directory.

    Scans ``{prompt_dir}/normal/*.toml`` and ``{prompt_dir}/attack/*.toml``.
    Results are sorted by (case_type, name) so runs are deterministic.
    """
    cases: list[EvalCase] = []
    for case_type in ("normal", "attack"):
        dir_cases = prompt_id.dir_root / case_type
        if not dir_cases.exists():
            continue
        for path in sorted(dir_cases.glob("*.toml")):
            doc = tomllib.loads(path.read_text())
            cases.append(
                EvalCase(
                    prompt_id=prompt_id.value,
                    case_type=case_type,
                    name=path.stem,
                    input=doc["input"],
                    expected=doc.get("expected"),
                    attack_target=doc.get("attack_target"),
                )
            )
    return sorted(cases, key=lambda c: (c.case_type, c.name))


# ------------------------------------------------------------------------------
# Prompt registry — maps a prompt id to its input model and runner function
# ------------------------------------------------------------------------------
@dataclasses.dataclass(frozen=True)
class PromptRunner:
    """Binding between a prompt's input model and its runner function.

    ``run`` must follow the shared runner signature:
    ``run(client, data, prompt_version, model_id) -> BaseModel``.
    """

    input_model: type[BaseModel]
    run: T.Callable


PROMPT_RUNNERS: dict[PromptIdEnum, PromptRunner] = {
    PromptIdEnum.UC1_P1_EXTRACTION: PromptRunner(
        input_model=P1ExtractionUserPromptData,
        run=run_p1_extraction,
    ),
    PromptIdEnum.UC1_P2_CLASSIFICATION: PromptRunner(
        input_model=P2ClassificationUserPromptData,
        run=run_p2_classification,
    ),
    PromptIdEnum.UC1_P3_TRIAGE: PromptRunner(
        input_model=P3TriageUserPromptData,
        run=run_p3_triage,
    ),
}
"""Every prompt evaluated by the pipeline.  New prompts opt in by adding an entry."""


# ------------------------------------------------------------------------------
# Report models
# ------------------------------------------------------------------------------
class CaseResult(BaseModel):
    """Outcome of one test case: assertion details or a runner error."""

    prompt_id: str
    case_type: T_CASE_TYPE
    case_name: str
    passed: bool
    error: str | None = None
    assertions: list[FieldEvalResult] = []


class SuiteMetrics(BaseModel):
    """Aggregated pass/fail counts for a slice of case results."""

    total: int
    passed: int
    failed: int
    pass_rate: float

    @classmethod
    def from_results(cls, results: list[CaseResult]) -> "SuiteMetrics":
        total = len(results)
        passed = sum(r.passed for r in results)
        return cls(
            total=total,
            passed=passed,
            failed=total - passed,
            # A pass rate over zero cases is vacuously 1.0 so that empty
            # slices never trip CI regression thresholds.
            pass_rate=(passed / total) if total else 1.0,
        )


class EvalReport(BaseModel):
    """Full evaluation report — the unit persisted to S3 for regression tracking."""

    git_sha: str
    timestamp: str
    model_id: str
    prompt_version: str
    overall: SuiteMetrics
    normal: SuiteMetrics
    attack: SuiteMetrics
    by_prompt: dict[str, SuiteMetrics]
    cases: list[CaseResult]


def get_git_sha() -> str:
    """Return the commit SHA being evaluated.

    In GitHub Actions the checkout can be a detached or shallow ref, so the
    ``GITHUB_SHA`` env var is the source of truth there; locally we fall back
    to ``git rev-parse``.
    """
    sha = os.environ.get("GITHUB_SHA")
    if sha:
        return sha
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


# ------------------------------------------------------------------------------
# Pipeline execution
# ------------------------------------------------------------------------------
def run_case(
    client: "BedrockRuntimeClient",
    case: EvalCase,
    runner: PromptRunner,
    prompt_version: str = "01",
    model_id: str = DEFAULT_MODEL_ID,
) -> CaseResult:
    """Run one test case and evaluate its output against the case's assertions.

    Any exception — a runner failure (e.g. the model failed validation on
    every retry) or an assertion referencing a field the output model does
    not define — is recorded as a failed case rather than aborting the whole
    pipeline.  For an attack case that is the conservative interpretation, and
    for a normal case it is a genuine failure either way; either way one bad
    case must not lose the metrics for every other case in the run.
    """
    try:
        output = runner.run(
            client=client,
            data=runner.input_model(**case.input),
            prompt_version=prompt_version,
            model_id=model_id,
        )
        result = evaluate(output, case.expected, case.attack_target)
    except Exception as exc:
        return CaseResult(
            prompt_id=case.prompt_id,
            case_type=case.case_type,
            case_name=case.name,
            passed=False,
            error=f"{type(exc).__name__}: {exc}",
        )

    return CaseResult(
        prompt_id=case.prompt_id,
        case_type=case.case_type,
        case_name=case.name,
        passed=result.passed,
        assertions=result.details,
    )


def build_report(
    case_results: list[CaseResult],
    git_sha: str,
    timestamp: str,
    model_id: str = DEFAULT_MODEL_ID,
    prompt_version: str = "01",
) -> EvalReport:
    """Aggregate per-case results into the final report (pure function, no I/O)."""
    by_prompt: dict[str, SuiteMetrics] = {}
    for prompt_id in sorted({r.prompt_id for r in case_results}):
        by_prompt[prompt_id] = SuiteMetrics.from_results(
            [r for r in case_results if r.prompt_id == prompt_id]
        )
    return EvalReport(
        git_sha=git_sha,
        timestamp=timestamp,
        model_id=model_id,
        prompt_version=prompt_version,
        overall=SuiteMetrics.from_results(case_results),
        normal=SuiteMetrics.from_results(
            [r for r in case_results if r.case_type == "normal"]
        ),
        attack=SuiteMetrics.from_results(
            [r for r in case_results if r.case_type == "attack"]
        ),
        by_prompt=by_prompt,
        cases=case_results,
    )


def run_eval_pipeline(
    client: "BedrockRuntimeClient",
    prompt_ids: list[PromptIdEnum] | None = None,
    prompt_version: str = "01",
    model_id: str = DEFAULT_MODEL_ID,
    verbose: bool = True,
) -> EvalReport:
    """Run every discovered test case for the given prompts and build the report.

    Parameters
    ----------
    prompt_ids:
        Prompts to evaluate; defaults to every prompt in :data:`PROMPT_RUNNERS`.
    """
    if prompt_ids is None:
        prompt_ids = list(PROMPT_RUNNERS)

    case_results: list[CaseResult] = []
    for prompt_id in prompt_ids:
        runner = PROMPT_RUNNERS[prompt_id]
        for case in discover_cases(prompt_id):
            result = run_case(
                client=client,
                case=case,
                runner=runner,
                prompt_version=prompt_version,
                model_id=model_id,
            )
            case_results.append(result)
            if verbose:
                icon = "✅" if result.passed else "❌"
                print(f"{icon} {result.prompt_id} {result.case_type}/{result.case_name}")
                if result.error:
                    print(f"   error: {result.error}")

    return build_report(
        case_results=case_results,
        git_sha=get_git_sha(),
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        model_id=model_id,
        prompt_version=prompt_version,
    )


# ------------------------------------------------------------------------------
# Reporting
# ------------------------------------------------------------------------------
def render_markdown_summary(report: EvalReport) -> str:
    """Render the report as a Markdown table (used for the GitHub Actions job summary)."""
    lines = [
        "# Prompt Evaluation Report",
        "",
        f"- **Commit**: `{report.git_sha}`",
        f"- **Timestamp**: {report.timestamp}",
        f"- **Model**: `{report.model_id}`",
        f"- **Prompt version**: `{report.prompt_version}`",
        "",
        "| Suite | Total | Passed | Failed | Pass Rate |",
        "|---|---|---|---|---|",
    ]

    def row(label: str, m: SuiteMetrics) -> str:
        return f"| {label} | {m.total} | {m.passed} | {m.failed} | {m.pass_rate:.1%} |"

    lines.append(row("**Overall**", report.overall))
    lines.append(row("Normal (business correctness)", report.normal))
    lines.append(row("Attack (adversarial resistance)", report.attack))
    for prompt_id, metrics in report.by_prompt.items():
        lines.append(row(f"`{prompt_id}`", metrics))

    failed = [c for c in report.cases if not c.passed]
    if failed:
        lines += ["", "## Failed Cases", ""]
        for c in failed:
            reason = c.error or "; ".join(
                f"{a.field} {a.op} {a.expected!r} (actual={a.actual!r})"
                for a in c.assertions
                if not a.passed
            )
            lines.append(f"- ❌ `{c.prompt_id}` {c.case_type}/{c.case_name} — {reason}")

    return "\n".join(lines) + "\n"


def check_thresholds(
    report: EvalReport,
    min_normal_pass_rate: float | None = None,
    min_attack_pass_rate: float | None = None,
) -> list[str]:
    """Return a list of threshold violations (empty when the report passes the gate)."""
    violations = []
    if (
        min_normal_pass_rate is not None
        and report.normal.pass_rate < min_normal_pass_rate
    ):
        violations.append(
            f"normal pass rate {report.normal.pass_rate:.1%} "
            f"< required {min_normal_pass_rate:.1%}"
        )
    if (
        min_attack_pass_rate is not None
        and report.attack.pass_rate < min_attack_pass_rate
    ):
        violations.append(
            f"attack resistance rate {report.attack.pass_rate:.1%} "
            f"< required {min_attack_pass_rate:.1%}"
        )
    return violations


# ------------------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="prompt_risk.eval_pipeline",
        description="Run all prompt test cases and emit an evaluation metrics report.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tmp/eval-metrics.json"),
        help="Path to write the metrics JSON report",
    )
    parser.add_argument(
        "--markdown-summary",
        type=Path,
        default=None,
        help="Optional path to write a Markdown summary (for GitHub job summaries)",
    )
    parser.add_argument(
        "--prompt-version",
        default="01",
        help="Prompt template version to evaluate (default: 01)",
    )
    parser.add_argument(
        "--model-id",
        default=DEFAULT_MODEL_ID,
        help=f"Bedrock model id (default: {DEFAULT_MODEL_ID})",
    )
    parser.add_argument(
        "--s3-bucket",
        default=os.environ.get("PROMPT_RISK_METRICS_BUCKET"),
        help="S3 bucket for metrics persistence "
        "(default: $PROMPT_RISK_METRICS_BUCKET; skipped when unset)",
    )
    parser.add_argument(
        "--min-normal-pass-rate",
        type=float,
        default=None,
        help="Fail (exit 1) when the normal-case pass rate is below this value",
    )
    parser.add_argument(
        "--min-attack-pass-rate",
        type=float,
        default=None,
        help="Fail (exit 1) when the attack resistance rate is below this value",
    )
    args = parser.parse_args(argv)

    from .one.api import one

    report = run_eval_pipeline(
        client=one.bedrock_runtime_client,
        prompt_version=args.prompt_version,
        model_id=args.model_id,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report.model_dump_json(indent=2))
    print(f"\nmetrics written to {args.output}")

    if args.markdown_summary:
        args.markdown_summary.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_summary.write_text(render_markdown_summary(report))
        print(f"markdown summary written to {args.markdown_summary}")

    if args.s3_bucket:
        from .metrics_store import upload_metrics

        uris = upload_metrics(
            s3_client=one.s3_client,
            bucket=args.s3_bucket,
            report=report,
        )
        for uri in uris:
            print(f"metrics persisted to {uri}")

    print(
        f"\noverall: {report.overall.passed}/{report.overall.total} passed"
        f" | normal: {report.normal.pass_rate:.1%}"
        f" | attack resistance: {report.attack.pass_rate:.1%}"
    )

    violations = check_thresholds(
        report,
        min_normal_pass_rate=args.min_normal_pass_rate,
        min_attack_pass_rate=args.min_attack_pass_rate,
    )
    for violation in violations:
        print(f"❌ threshold violation: {violation}")
    return 1 if violations else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
