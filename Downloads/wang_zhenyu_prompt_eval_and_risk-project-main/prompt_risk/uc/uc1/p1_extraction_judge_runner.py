# -*- coding: utf-8 -*-

"""
UC1-P1 extraction judge runner — evaluate P1 extraction output quality.
"""

import typing as T
import json
from pydantic import BaseModel, Field, ValidationError

from ...constants import PromptIdEnum
from ...prompts import Prompt
from ...llm_output import extract_json
from ...bedrock_utils import converse

if T.TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime import BedrockRuntimeClient


class FieldError(BaseModel):
    field: str = Field(description="Name of the field that failed validation")
    issue: str = Field(description="Description of what is wrong")


class P1ExtractionJudgeUserPromptData(BaseModel):
    input: str
    output: str


class P1ExtractionJudgeOutput(BaseModel):
    """Structured output for the P1 extraction judge prompt."""

    pass_: bool = Field(alias="pass", description="Whether all quality criteria are met")
    reason: str = Field(description="Explanation of the judgment")
    field_errors: list[FieldError] = Field(
        default_factory=list,
        description="Fields that failed validation and why",
    )

    model_config = {"populate_by_name": True}


MAX_RETRIES = 3


def run_p1_extraction_judge(
    client: "BedrockRuntimeClient",
    data: P1ExtractionJudgeUserPromptData,
    prompt_version: str = "01",
    model_id: str = "us.amazon.nova-2-lite-v1:0",
) -> P1ExtractionJudgeOutput:
    """Execute the P1 extraction judge prompt and return validated output.

    Follows the same caching and retry strategy as
    :func:`~prompt_risk.uc.uc1.p1_extraction_runner.run_p1_extraction`.
    """
    prompt = Prompt(
        id=PromptIdEnum.UC1_P1_EXTRACTION_JUDGE.value, version=prompt_version
    )

    system = [
        {"text": prompt.system_prompt_template.render()},
        {"cachePoint": {"type": "default"}},
    ]
    user_prompt = prompt.user_prompt_template.render(data=data)
    messages: list[dict] = [
        {"role": "user", "content": [{"text": user_prompt}]},
    ]

    for attempt in range(MAX_RETRIES):
        text = converse(client, model_id, system, messages)
        json_obj = extract_json(text)

        try:
            return P1ExtractionJudgeOutput(**json_obj)
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
