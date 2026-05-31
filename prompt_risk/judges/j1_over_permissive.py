# -*- coding: utf-8 -*-

"""
J1 Over-Permissive Authorization Judge.

Evaluates a prompt's system prompt text (and optionally its user prompt
template) for over-permissive authorization risks.  The judge itself is a
prompt — it uses an LLM to perform semantic analysis against five criteria
defined in its own system prompt template.

This module is **use-case-agnostic**.  It accepts raw prompt text as strings
and knows nothing about FNOL, claims, or any specific business domain.
Use-case-specific wrappers (e.g. ``uc.uc1.j1_uc1_p1``) handle loading
prompt files and calling this function.
"""

import typing as T
import json
import re

from pydantic import BaseModel, Field, ValidationError

from ..constants import PromptIdEnum
from ..prompts import Prompt
from ..llm_output import extract_json
from ..bedrock_utils import converse

if T.TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime import BedrockRuntimeClient


# ---------------------------------------------------------------------------
# Input / Output models
# ---------------------------------------------------------------------------
class J1UserPromptData(BaseModel):
    """Input data for the J1 judge user prompt template."""

    target_system_prompt: str
    target_user_prompt_template: T.Optional[str] = None


T_SEVERITY = T.Literal["major", "minor", "pass"]
T_OVERALL_RISK = T.Literal["critical", "high", "medium", "low", "pass"]


class J1Finding(BaseModel):
    """A single criterion-level finding from the J1 judge."""

    criterion: str
    severity: T_SEVERITY
    evidence: str
    explanation: str
    recommendation: str


class J1Result(BaseModel):
    """Complete J1 judge evaluation result."""

    overall_risk: T_OVERALL_RISK
    score: int = Field(ge=1, le=5)
    findings: list[J1Finding]
    summary: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
MAX_RETRIES = 3


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def run_j1_over_permissive(
    client: "BedrockRuntimeClient",
    data: J1UserPromptData,
    judge_version: str = "01",
    model_id: str = "us.amazon.nova-2-lite-v1:0",
) -> J1Result:
    """Evaluate a prompt for over-permissive authorization risks.

    Parameters
    ----------
    client:
        Bedrock Runtime client.
    data:
        The target prompt texts to evaluate.
    judge_version:
        Which version of the J1 judge prompt to use.
    model_id:
        Bedrock model ID for the judge LLM.

    Returns
    -------
    J1Result
        Structured evaluation result with overall risk, score, findings,
        and summary.
    """
    judge_prompt = Prompt(
        id=PromptIdEnum.JUDGE_J1_OVER_PERMISSIVE.value,
        version=judge_version,
    )

    system = [
        {"text": judge_prompt.system_prompt_template.render()},
        {"cachePoint": {"type": "default"}},
    ]

    user_prompt = judge_prompt.user_prompt_template.render(data=data)

    messages: list[dict] = [
        {"role": "user", "content": [{"text": user_prompt}]},
    ]

    for attempt in range(MAX_RETRIES):
        text = converse(client, model_id, system, messages)
        json_obj = extract_json(text)
        try:
            return J1Result(**json_obj)
        except (json.JSONDecodeError, ValidationError) as exc:
            if attempt == MAX_RETRIES - 1:
                raise

            error_msg = (
                f"Your previous response failed validation:\n{exc}\n\n"
                "Please return a corrected JSON object."
            )
            messages.append({"role": "assistant", "content": [{"text": text}]})
            messages.append({"role": "user", "content": [{"text": error_msg}]})

    raise Exception("Should never reach this line of code")  # pragma: no cover


# ---------------------------------------------------------------------------
# Pretty-print
# ---------------------------------------------------------------------------
_SEVERITY_ICON = {"pass": "✅", "minor": "⚠️", "major": "❌"}
_RISK_ICON = {"pass": "✅", "low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}


def print_j1_result(result: J1Result) -> None:
    """Print J1 evaluation result to stdout."""
    for f in result.findings:
        icon = _SEVERITY_ICON.get(f.severity, "?")
        print(f"  {icon} [{f.severity.upper()}] {f.criterion}")
        print(f"      Evidence: {f.evidence}")
        print(f"      Explanation: {f.explanation}")
        if f.severity != "pass":
            print(f"      Recommendation: {f.recommendation}")
    risk_icon = _RISK_ICON.get(result.overall_risk, "?")
    print(f"  {risk_icon} Overall: {result.overall_risk.upper()} (score {result.score}/5)")
    print(f"  Summary: {result.summary}")
