# -*- coding: utf-8 -*-

"""
UC1-P2 classification runner — classify line of business from P1 extraction output.
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

T_LINE_OF_BUSINESS = T.Literal[
    "auto",
    "property",
    "workers_comp",
    "general_liability",
    "marine",
    "cyber",
    "other",
]
T_CONFIDENCE = T.Literal[
    "high",
    "medium",
    "low",
]


class P2ClassificationUserPromptData(BaseModel):
    extraction_json: str


class P2ClassificationOutput(BaseModel):
    """Structured output for the P2 LoB classification prompt."""

    # fmt: off
    line_of_business: T_LINE_OF_BUSINESS = Field(description="Primary line of business")
    confidence: T_CONFIDENCE = Field(description="Classification confidence: high, medium, or low")
    reasoning: str = Field(description="One sentence explaining the classification")
    secondary_lob: T_LINE_OF_BUSINESS | T.Literal["none"] = Field(description="Secondary LoB if applicable, otherwise 'none'")
    field_conflicts: list[str] = Field(description="Inconsistencies detected between fields; empty list if none")
    escalate: bool = Field(description="True if conflicts detected or data too contradictory to classify reliably")
    # fmt: on


MAX_RETRIES = 3
"""Maximum number of converse API calls per :func:`run_p2_classification` invocation."""


def run_p2_classification(
    client: "BedrockRuntimeClient",
    data: P2ClassificationUserPromptData,
    prompt_version: str = "01",
    model_id: str = "us.amazon.nova-2-lite-v1:0",
) -> P2ClassificationOutput:
    """Execute the P2 classification prompt and return validated output.

    Takes the structured JSON output from P1 extraction and classifies the
    claim's line of business.

    Uses the same system-prompt caching and retry-on-validation-failure
    pattern as :func:`~prompt_risk.uc.uc1.p1_extraction_runner.run_p1_extraction`.
    """
    prompt = Prompt(id=PromptIdEnum.UC1_P2_CLASSIFICATION.value, version=prompt_version)

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
            return P2ClassificationOutput(**json_obj)
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
