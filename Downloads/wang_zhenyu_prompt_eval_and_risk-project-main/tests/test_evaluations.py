# -*- coding: utf-8 -*-

from pydantic import BaseModel
from prompt_risk.evaluations import evaluate, EvalResult, FieldEvalResult


class _FakeOutput(BaseModel):
    date_of_loss: str = "2026-04-15"
    injury_indicator: str = "severe"
    estimated_severity: str = "high"
    police_report: str = "HPD-001"


class TestEvaluateExpected:
    def test_all_match(self):
        output = _FakeOutput()
        result = evaluate(output, expected={"date_of_loss": "2026-04-15", "police_report": "HPD-001"})
        assert result.passed is True
        assert len(result.details) == 2
        assert all(d.op == "eq" and d.passed for d in result.details)

    def test_mismatch(self):
        output = _FakeOutput()
        result = evaluate(output, expected={"date_of_loss": "2026-01-01"})
        assert result.passed is False
        assert result.details[0].actual == "2026-04-15"
        assert result.details[0].expected == "2026-01-01"

    def test_partial_mismatch(self):
        output = _FakeOutput()
        result = evaluate(
            output,
            expected={"date_of_loss": "2026-04-15", "police_report": "WRONG"},
        )
        assert result.passed is False
        assert result.details[0].passed is True
        assert result.details[1].passed is False


class TestEvaluateAttackTarget:
    def test_not_compromised(self):
        output = _FakeOutput()
        result = evaluate(output, attack_target={"injury_indicator": "none", "estimated_severity": "low"})
        assert result.passed is True
        assert all(d.op == "ne" and d.passed for d in result.details)

    def test_compromised(self):
        output = _FakeOutput(injury_indicator="none")
        result = evaluate(output, attack_target={"injury_indicator": "none"})
        assert result.passed is False
        assert result.details[0].passed is False


class TestEvaluateCombined:
    def test_both_pass(self):
        output = _FakeOutput()
        result = evaluate(
            output,
            expected={"date_of_loss": "2026-04-15"},
            attack_target={"injury_indicator": "none"},
        )
        assert result.passed is True
        assert len(result.details) == 2

    def test_expected_pass_attack_fail(self):
        output = _FakeOutput(injury_indicator="none")
        result = evaluate(
            output,
            expected={"date_of_loss": "2026-04-15"},
            attack_target={"injury_indicator": "none"},
        )
        assert result.passed is False
        eq_results = [d for d in result.details if d.op == "eq"]
        ne_results = [d for d in result.details if d.op == "ne"]
        assert eq_results[0].passed is True
        assert ne_results[0].passed is False


class TestEvaluateEdgeCases:
    def test_no_assertions(self):
        output = _FakeOutput()
        result = evaluate(output)
        assert result.passed is True
        assert result.details == []

    def test_none_arguments(self):
        output = _FakeOutput()
        result = evaluate(output, expected=None, attack_target=None)
        assert result.passed is True
        assert result.details == []


if __name__ == "__main__":
    from prompt_risk.tests import run_cov_test

    run_cov_test(
        __file__,
        "prompt_risk.evaluations",
        preview=False,
    )
