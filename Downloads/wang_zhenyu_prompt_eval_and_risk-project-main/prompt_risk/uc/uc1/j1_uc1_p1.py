# -*- coding: utf-8 -*-

"""
Wrapper: run J1 Over-Permissive Authorization Judge on UC1-P1 extraction prompt.

This module bridges the use-case-specific prompt loading (UC1-P1 versions)
with the generic J1 judge.  It uses the P1 test data loader to render the
user prompt with real test data, so the judge evaluates a concrete prompt
rather than a raw Jinja template with placeholders.
"""

import typing as T

from ...constants import PromptIdEnum
from ...prompts import Prompt
from ...judges.j1_over_permissive import (
    J1UserPromptData,
    J1Result,
    run_j1_over_permissive,
)
from .p1_test_data import P1ExtractionUserPromptDataLoader

if T.TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime import BedrockRuntimeClient


def run_j1_on_uc1_p1(
    client: "BedrockRuntimeClient",
    prompt_version: str = "01",
    loader: T.Optional[P1ExtractionUserPromptDataLoader] = None,
    judge_version: str = "01",
    model_id: str = "us.amazon.nova-2-lite-v1:0",
) -> J1Result:
    """Run J1 judge on a specific version of the UC1-P1 extraction prompt.

    Parameters
    ----------
    client:
        Bedrock Runtime client.
    prompt_version:
        Version of the UC1-P1 prompt to evaluate (e.g. "01", "02").
    loader:
        Optional test data loader. When provided, the user prompt template
        is rendered with real FNOL data. When omitted, the judge evaluates
        the system prompt only.
    judge_version:
        Version of the J1 judge prompt to use.
    model_id:
        Bedrock model ID for the judge LLM.
    """
    prompt = Prompt(id=PromptIdEnum.UC1_P1_EXTRACTION.value, version=prompt_version)

    user_prompt_text = None
    if loader is not None:
        user_prompt_text = prompt.user_prompt_template.render(data=loader.data)

    data = J1UserPromptData(
        target_system_prompt=prompt.system_prompt_content,
        target_user_prompt_template=user_prompt_text,
    )

    return run_j1_over_permissive(
        client=client,
        data=data,
        judge_version=judge_version,
        model_id=model_id,
    )
