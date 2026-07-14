# -*- coding: utf-8 -*-

from pydantic import BaseModel

from prompt_risk import eval_pipeline
from prompt_risk.eval_pipeline import (
    PROMPT_RUNNERS,
    CaseResult,
    EvalCase,
    PromptRunner,
    SuiteMetrics,
    build_report,
    check_thresholds,
    discover_cases,
    render_markdown_summary,
    run_case,
)


class TestDiscoverCases:
    def test_every_registered_prompt_has_cases(self):
        for prompt_id in PROMPT_RUNNERS:
            cases = discover_cases(prompt_id)
            case_types = {c.case_type for c in cases}
            assert len(cases) > 0
            assert case_types == {"normal", "attack"}

    def test_every_case_toml_is_well_formed(self):
        # Every discovered TOML must construct its prompt's input model and
        # carry at least one assertion — this keeps newly added test-case
        # files honest without any hand-registration.
        for prompt_id, runner in PROMPT_RUNNERS.items():
            for case in discover_cases(prompt_id):
                runner.input_model(**case.input)
                assert case.expected or case.attack_target, (
                    f"{case.prompt_id} {case.case_type}/{case.name} "
                    "has no assertions"
                )

    def test_attack_cases_have_attack_target(self):
        for prompt_id in PROMPT_RUNNERS:
            for case in discover_cases(prompt_id):
                if case.case_type == "attack":
                    assert case.attack_target


class FakeInput(BaseModel):
    narrative: str


class FakeOutput(BaseModel):
    severity: str


def make_fake_runner(output: FakeOutput | None = None) -> PromptRunner:
    def run(client, data, prompt_version, model_id):
        if output is None:
            raise ValueError("model exploded")
        return output

    return PromptRunner(input_model=FakeInput, run=run)


def make_case(**overrides) -> EvalCase:
    kwargs = dict(
        prompt_id="uc1:p1",
        case_type="normal",
        name="b-01",
        input={"narrative": "hello"},
        expected={"severity": "low"},
    )
    kwargs.update(overrides)
    return EvalCase(**kwargs)


class TestRunCase:
    def test_passing_case(self):
        result = run_case(
            client=None,
            case=make_case(),
            runner=make_fake_runner(FakeOutput(severity="low")),
        )
        assert result.passed is True
        assert result.error is None
        assert len(result.assertions) == 1

    def test_attack_case_resisted_and_compromised(self):
        case = make_case(
            case_type="attack",
            expected=None,
            attack_target={"severity": "low"},
        )
        resisted = run_case(
            client=None,
            case=case,
            runner=make_fake_runner(FakeOutput(severity="high")),
        )
        assert resisted.passed is True

        compromised = run_case(
            client=None,
            case=case,
            runner=make_fake_runner(FakeOutput(severity="low")),
        )
        assert compromised.passed is False

    def test_runner_error_is_recorded_as_failure(self):
        result = run_case(
            client=None,
            case=make_case(),
            runner=make_fake_runner(output=None),
        )
        assert result.passed is False
        assert "model exploded" in result.error

    def test_assertion_on_missing_field_is_recorded_not_raised(self):
        # A TOML typo that asserts on a field the output model lacks must
        # degrade to a failed case, not crash the whole pipeline.
        result = run_case(
            client=None,
            case=make_case(expected={"nonexistent_field": "x"}),
            runner=make_fake_runner(FakeOutput(severity="low")),
        )
        assert result.passed is False
        assert "nonexistent_field" in result.error


def make_results() -> list[CaseResult]:
    return [
        CaseResult(prompt_id="uc1:p1", case_type="normal", case_name="b-01", passed=True),
        CaseResult(prompt_id="uc1:p1", case_type="normal", case_name="b-02", passed=False),
        CaseResult(prompt_id="uc1:p1", case_type="attack", case_name="a-01", passed=True),
        CaseResult(prompt_id="uc1:p2", case_type="attack", case_name="a-01", passed=True),
    ]


class TestBuildReport:
    def test_aggregation(self):
        report = build_report(
            case_results=make_results(),
            git_sha="abcdef1234567890",
            timestamp="2026-07-14T00:00:00Z",
        )
        assert report.overall.total == 4
        assert report.overall.passed == 3
        assert report.normal.total == 2
        assert report.normal.pass_rate == 0.5
        assert report.attack.total == 2
        assert report.attack.pass_rate == 1.0
        assert set(report.by_prompt) == {"uc1:p1", "uc1:p2"}
        assert report.by_prompt["uc1:p1"].total == 3

    def test_empty_slice_pass_rate_is_vacuous(self):
        assert SuiteMetrics.from_results([]).pass_rate == 1.0


class TestCheckThresholds:
    def test_violations(self):
        report = build_report(
            case_results=make_results(),
            git_sha="abc",
            timestamp="2026-07-14T00:00:00Z",
        )
        assert check_thresholds(report) == []
        assert check_thresholds(report, min_attack_pass_rate=1.0) == []
        violations = check_thresholds(
            report,
            min_normal_pass_rate=0.8,
            min_attack_pass_rate=1.0,
        )
        assert len(violations) == 1
        assert "normal pass rate" in violations[0]


class TestRenderMarkdownSummary:
    def test_contains_metrics_and_failures(self):
        report = build_report(
            case_results=make_results(),
            git_sha="abc",
            timestamp="2026-07-14T00:00:00Z",
        )
        md = render_markdown_summary(report)
        assert "| **Overall** | 4 | 3 | 1 |" in md
        assert "## Failed Cases" in md
        assert "b-02" in md


if __name__ == "__main__":
    from prompt_risk.tests import run_cov_test

    run_cov_test(
        __file__,
        "prompt_risk.eval_pipeline",
        preview=False,
    )
