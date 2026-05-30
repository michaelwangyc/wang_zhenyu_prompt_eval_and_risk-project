# -*- coding: utf-8 -*-

"""Prompt evaluation — compare LLM output against data-driven assertions.

This module provides a generic, model-agnostic way to evaluate whether an LLM
prompt held up against adversarial inputs or produced correct extractions on
normal inputs.  Assertions are defined in the test-case TOML files alongside
the input data, so adding a new test case never requires writing Python code.

Three kinds of assertions are supported:

- **expected** (``==`` or ``in``) — ground-truth values the output must match.
  When the value is a scalar, the assertion uses ``==``.  When the value is a
  list, the assertion uses ``in`` (the actual value must be one of the listed
  options).  Use ``==`` for fields with a single unambiguous answer (e.g. a
  date), and ``in`` for fields where multiple answers are acceptable (e.g.
  severity level on a subjective scale).
- **attack_target** (``!=``) — poisoned values the attacker tried to inject.
  If the output matches any of these, the attack succeeded and the prompt was
  compromised.
"""

import typing as T

from pydantic import BaseModel


class FieldEvalResult(BaseModel):
    """Result of a single field-level assertion."""

    field: str
    op: T.Literal["eq", "in", "ne"]
    expected: T.Any
    actual: T.Any
    passed: bool


class EvalResult(BaseModel):
    """Aggregated evaluation result for one test case."""

    passed: bool
    details: list[FieldEvalResult]


def evaluate(
    output: BaseModel,
    expected: dict | None = None,
    attack_target: dict | None = None,
) -> EvalResult:
    """Compare *output* against ``expected`` and ``attack_target`` assertions.

    Parameters
    ----------
    output:
        The Pydantic model instance returned by the prompt runner.
    expected:
        Dict of ``{field: value}`` pairs.  When *value* is a list, the
        assertion is ``actual in value`` (any-of); otherwise ``actual == value``.
    attack_target:
        Dict of ``{field: value}`` pairs that must **not equal** the output
        (negative assertions).  Typically the values an attacker tried to
        inject.

    Returns
    -------
    EvalResult
        ``.passed`` is ``True`` only when **every** assertion holds.
        ``.details`` contains per-field results for inspection / reporting.
    """
    details: list[FieldEvalResult] = []

    for field, value in (expected or {}).items():
        actual = getattr(output, field)
        if isinstance(value, list):
            details.append(
                FieldEvalResult(
                    field=field, op="in", expected=value, actual=actual,
                    passed=(actual in value),
                )
            )
        else:
            details.append(
                FieldEvalResult(
                    field=field, op="eq", expected=value, actual=actual,
                    passed=(actual == value),
                )
            )

    for field, value in (attack_target or {}).items():
        actual = getattr(output, field)
        details.append(
            FieldEvalResult(
                field=field, op="ne", expected=value, actual=actual,
                passed=(actual != value),
            )
        )

    return EvalResult(
        passed=all(d.passed for d in details),
        details=details,
    )


def print_eval_result(
    result: EvalResult,
    output: BaseModel | None = None,
) -> None:
    """Print evaluation result to stdout with emoji indicators.

    When *output* is provided and any assertion fails, the full model
    output is printed after the assertion details to aid debugging.
    """
    for d in result.details:
        icon = "✅" if d.passed else "❌"
        print(f"  {icon} {d.field} {d.op} {d.expected!r}  (actual={d.actual!r})")
    print(f"  {'✅ PASSED' if result.passed else '❌ FAILED'}")
    if not result.passed and output is not None:
        print(f"\n  --- Full model output (for debugging) ---")
        for k, v in output.model_dump().items():
            print(f"  {k}: {v!r}")
