# -*- coding: utf-8 -*-

"""
J5 Logic Ambiguity Judge.

Evaluates a prompt for logical gaps, undefined edge cases, ambiguous conditions,
and incomplete decision trees that could lead to unpredictable or unsafe behavior.
"""

import typing as T
import json

from pydantic import BaseModel, Field, ValidationError

from ..constants import PromptIdEnum
from ..prompts import Prompt
from ..llm_output import extract_json
from ..bedrock_utils import converse

if T.TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime import BedrockRuntimeClient


class J5UserPromptData(BaseModel):
    """Input data for the J5 judge user prompt template."""

    target_system_prompt: str
    target_user_prompt_template: T.Optional[str] = None


T_SEVERITY = T.Literal["major", "minor", "pass"]
T_OVERALL_RISK = T.Literal["critical", "high", "medium", "low", "pass"]


class J5Finding(BaseModel):
    criterion: str
    severity: T_SEVERITY
    evidence: str
    explanation: str
    recommendation: str


class J5Result(BaseModel):
    overall_risk: T_OVERALL_RISK
    score: int = Field(ge=1, le=5)
    findings: list[J5Finding]
    summary: str


MAX_RETRIES = 3


def run_j5_logic_ambiguity(
    client: "BedrockRuntimeClient",
    data: J5UserPromptData,
    judge_version: str = "01",
    model_id: str = "us.amazon.nova-2-lite-v1:0",
) -> J5Result:
    """Evaluate a prompt for logical gaps, ambiguities, and undefined edge cases."""
    judge_prompt = Prompt(
        id=PromptIdEnum.JUDGE_J5_LOGIC_AMBIGUITY.value,
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
            return J5Result(**json_obj)
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


_SEVERITY_ICON = {"pass": "✅", "minor": "⚠️", "major": "❌"}
_RISK_ICON = {"pass": "✅", "low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}


def print_j5_result(result: J5Result) -> None:
    """Print J5 evaluation result to stdout."""
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
