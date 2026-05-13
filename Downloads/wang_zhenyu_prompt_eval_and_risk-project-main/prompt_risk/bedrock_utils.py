# -*- coding: utf-8 -*-

"""
Bedrock Converse API wrapper.
"""

import typing as T

if T.TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime import BedrockRuntimeClient

def converse(
    client: "BedrockRuntimeClient",
    model_id: str,
    system: list[dict],
    messages: list[dict],
) -> str:
    """Call Bedrock Converse API and return the assistant's text response."""
    response = client.converse(
        modelId=model_id,
        system=system,
        messages=messages,
    )
    return response["output"]["message"]["content"][0]["text"]