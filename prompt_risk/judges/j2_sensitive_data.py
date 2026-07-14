# -*- coding: utf-8 -*-

"""
J2 Sensitive Data Judge.

Evaluates a prompt for sensitive data exposure risks — PII, financial data,
health records, credentials, and other regulated or confidential information.
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


class J2UserPromptData(BaseModel):
    """Input data for the J2 judge user prompt template."""

    target_system_prompt: str
    target_user_prompt_template: T.Optional[str] = None


T_SEVERITY = T.Literal["major", "minor", "pass"]
T_OVERALL_RISK = T.Literal["critical", "high", "medium", "low", "pass"]


class J2Finding(BaseModel):
    criterion: str
    severity: T_SEVERITY
    evidence: str
    explanation: str
    recommendation: str


class J2Result(BaseModel):
    overall_risk: T_OVERALL_RISK
    score: int = Field(ge=1, le=5)
    findings: list[J2Finding]
    summary: str


MAX_RETRIES = 3


def run_j2_sensitive_data(
    client: "BedrockRuntimeClient",
    data: J2UserPromptData,
    judge_version: str = "01",
    model_id: str = "us.amazon.nova-2-lite-v1:0",
) -> J2Result:
    """Evaluate a prompt for sensitive data exposure risks."""
    judge_prompt = Prompt(
        id=PromptIdEnum.JUDGE_J2_SENSITIVE_DATA.value,
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
            return J2Result(**json_obj)
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


def print_j2_result(result: J2Result) -> None:
    """Print J2 evaluation result to stdout."""
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
