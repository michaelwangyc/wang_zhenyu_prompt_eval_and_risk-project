# -*- coding: utf-8 -*-

"""
UC1-P1 extraction runner — execute the FNOL extraction prompt and parse output.
"""

import typing as T
import json
import re
from pydantic import BaseModel, Field, ValidationError, field_validator

from ...constants import PromptIdEnum
from ...prompts import Prompt
from ...llm_output import extract_json
from ...bedrock_utils import converse

if T.TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime import BedrockRuntimeClient

T_INJURY_INDICATOR = T.Literal["none", "minor", "moderate", "severe", "fatal"]
T_ESTIMATE_SEVERITY = T.Literal["low", "medium", "high"]


class P1ExtractionUserPromptData(BaseModel):
    source: str
    narrative: str


class P1ExtractionOutput(BaseModel):
    """Structured output for the P1 FNOL extraction prompt.

    Each field mirrors the JSON schema specified in the system prompt.
    Pydantic validators enforce that the model returns values within the
    expected formats and enumerations.  When validation fails, the retry
    loop in :func:`run` feeds the error back to the model so it can
    self-correct — see :func:`run` for details.
    """

    # fmt: off
    date_of_loss: str = Field(description="Date of the incident (YYYY-MM-DD or 'unknown')")
    time_of_loss: str = Field(description="Time of the incident (HH:MM 24-hour or 'unknown')")
    location: str = Field(description="Where the incident occurred")
    line_of_business_hint: str = Field(description="One of auto, property, workers_comp, general_liability, or ambiguous")
    parties_involved: list[str] = Field(description="List of party roles")
    damage_description: str = Field(description="Brief summary of damage")
    injury_indicator: T_INJURY_INDICATOR = Field(description="none, minor, moderate, severe, or fatal")
    police_report: str = Field(description="Report number if mentioned, otherwise 'none'")
    evidence_available: list[str] = Field(description="List of available evidence types")
    estimated_severity: T_ESTIMATE_SEVERITY = Field(description="low, medium, or high")
    # fmt: on

    @field_validator("date_of_loss")
    @classmethod
    def validate_date_of_loss(cls, v: str) -> str:
        if v == "unknown":
            return v
        from datetime import datetime

        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f"date_of_loss must be 'YYYY-MM-DD' or 'unknown', got '{v}'"
            )
        return v


MAX_RETRIES = 3
"""Maximum number of converse API calls per :func:`run` invocation.

LLM output is non-deterministic — even with a well-crafted prompt, the model
may occasionally return values that violate the output schema (e.g. a date in
``MM/DD/YYYY`` instead of ``YYYY-MM-DD``, or a severity string outside the
allowed enum).  Rather than failing immediately, we feed the Pydantic
validation error back to the model as a follow-up user message so it can
self-correct.  Three attempts strikes a balance between resilience and cost:
most fixable errors resolve on the second try, and a third guards against
edge cases without runaway API spend.
"""


def run_p1_extraction(
    client: "BedrockRuntimeClient",
    data: P1ExtractionUserPromptData,
    prompt_version: str = "01",
    model_id: str = "us.amazon.nova-2-lite-v1:0",
) -> P1ExtractionOutput:
    """Execute the P1 extraction prompt and return validated output.

    **System prompt caching** — The system prompt is static (no Jinja
    variables) by design.  This lets us place a ``cachePoint`` after it so
    that Bedrock caches the prefix across calls.  When the same system
    prompt is reused — whether across retries within a single ``run_p1_extraction()``
    call or across independent invocations — subsequent requests hit the
    cache and skip redundant input processing, reducing both latency and
    cost.

    **Why the user prompt is NOT cached** — The user prompt contains the
    per-request FNOL narrative and is different for every claim.  Caching
    it would incur a cache-write cost on every call with virtually zero
    chance of a cache hit, making it a net loss.  During retries the user
    prompt is already present in the ``messages`` history, so the model
    sees it without any extra caching mechanism.

    **Retry on validation failure** — LLM output is non-deterministic.
    When Pydantic validation fails (e.g. wrong date format, invalid enum
    value), we append the model's raw reply as an ``assistant`` message
    and the validation error as a ``user`` message, then call the API
    again.  This gives the model concrete feedback on what went wrong so
    it can self-correct.  We allow up to ``MAX_RETRIES`` attempts; if all
    fail, the last exception is re-raised.
    """
    prompt = Prompt(id=PromptIdEnum.UC1_P1_EXTRACTION.value, version=prompt_version)

    # System prompt is static — attach a cachePoint so Bedrock can reuse
    # the cached prefix across calls (retries and independent invocations).
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
            return P1ExtractionOutput(**json_obj)
        except (json.JSONDecodeError, ValidationError) as exc:
            if attempt == MAX_RETRIES - 1:
                raise

            # Feed the validation error back so the model can self-correct.
            error_msg = (
                f"Your previous response failed validation:\n{exc}\n\n"
                "Please return a corrected JSON object."
            )
            messages.append({"role": "assistant", "content": [{"text": text}]})
            messages.append({"role": "user", "content": [{"text": error_msg}]})

    raise Exception("Should never reach this line of code")  # pragma: no cover
