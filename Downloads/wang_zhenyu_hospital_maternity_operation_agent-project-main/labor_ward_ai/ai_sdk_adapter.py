# -*- coding: utf-8 -*-

"""
Adapter module for converting Vercel AI SDK format to AWS Bedrock format.

This module bridges the gap between the frontend (using Vercel AI SDK) and
the backend (using AWS Bedrock). It transforms message structures from
AI SDK's format into Bedrock Converse API's expected format.

The Vercel AI SDK sends messages in a specific format with 'parts' (for
multi-modal content support), while Bedrock expects a different structure.
This adapter handles that translation.

Dependencies:
- vercel_ai_sdk_mate: https://pypi.org/project/vercel-ai-sdk-mate/
  Provides typed dataclass wrappers for Vercel AI SDK request/response formats,
  making it easier to work with the JSON data from the frontend.
"""

import sys
import json
import uuid

from fastapi import Request
import vercel_ai_sdk_mate.api as vercel_ai_sdk_mate

from .utils import debug


def part_to_bedrock_content(part: vercel_ai_sdk_mate.T_PART) -> dict:
    """
    Convert an AI SDK message part to Bedrock content block format.

    AI SDK uses 'parts' to support multi-modal content (text, images, etc.).
    This function converts each part to Bedrock's content block format.

    Args:
        part: A message part from AI SDK (text, image, etc.).

    Returns:
        dict: Bedrock content block (e.g., {"text": "Hello"}).

    Raises:
        TypeError: If the part type is not supported (e.g., image, file).
    """
    if part.type == vercel_ai_sdk_mate.MessagePartTypeEnum.TEXT.value:
        return {"text": part.text}
    else:
        # Currently only text is supported; extend here for images, files, etc.
        raise TypeError(f"Unsupported part type: {part.type}")


def message_to_bedrock_message(message: vercel_ai_sdk_mate.Message) -> dict | None:
    """
    Convert an AI SDK message to Bedrock message format.

    Handles role mapping between AI SDK and Bedrock:
    - AI SDK 'user' -> Bedrock 'user'
    - AI SDK 'assistant' -> Bedrock 'assistant'
    - AI SDK 'system' -> Skipped (Bedrock handles system prompts separately)

    Args:
        message: An AI SDK message object containing role and parts.

    Returns:
        dict: Bedrock message format with 'role' and 'content' fields,
              or None if the role is not mappable (e.g., system).
    """
    # Map AI SDK roles to Bedrock roles
    # Note: Bedrock Converse API handles system prompts separately,
    # so there's no direct mapping for the 'system' role
    ai_sdk_role_to_bedrock_role_mapping = {
        vercel_ai_sdk_mate.MessageRoleEnum.USER.value: "user",
        vercel_ai_sdk_mate.MessageRoleEnum.ASSISTANT.value: "assistant",
    }

    if message.role in ai_sdk_role_to_bedrock_role_mapping:
        return {
            "role": ai_sdk_role_to_bedrock_role_mapping[message.role],
            "content": [part_to_bedrock_content(part) for part in message.parts],
        }
    else:
        # Skip messages with unmapped roles (e.g., system messages)
        return None


def request_body_to_bedrock_converse_messages(
    request_body: vercel_ai_sdk_mate.RequestBody,
) -> list[dict]:
    """
    Convert an entire AI SDK request body to Bedrock message list.

    This is the main entry point for converting frontend chat history
    into Bedrock's expected format. It processes all messages in the
    request and filters out any that can't be mapped.

    Args:
        request_body: The parsed request body from the AI SDK frontend,
                      containing the full conversation history.

    Returns:
        list[dict]: List of Bedrock-formatted messages ready for the
                    Converse API's 'messages' parameter.

    Example:
        >>> request_body = RequestBody(**await request.json())
        >>> bedrock_messages = request_body_to_bedrock_converse_messages(request_body)
        >>> # bedrock_messages can now be passed to ChatSession
    """
    messages = []
    for message in request_body.messages:
        bedrock_message = message_to_bedrock_message(message)
        if bedrock_message is not None:
            messages.append(bedrock_message)
    return messages


def get_last_user_message_text(request_body: vercel_ai_sdk_mate.RequestBody) -> str | None:
    """
    Extract the text content from the last user message in the request.

    This is useful for validation (e.g., message length check) before
    processing. Returns None if extraction fails for any reason, allowing
    the caller to gracefully skip validation rather than crash.

    Args:
        request_body: The parsed AI SDK request body.

    Returns:
        str: The text content of the last user message.
        None: If extraction fails (no messages, wrong format, etc.).
    """
    try:
        # The last message in the list is always the user's latest input
        last_message = request_body.messages[-1]
        # AI SDK stores text in parts[0].text for text messages
        return last_message.parts[0].text
    except (IndexError, AttributeError, TypeError):
        # If anything goes wrong, return None to skip validation
        return None


def request_body_to_agent_history(
    request_body: vercel_ai_sdk_mate.RequestBody,
) -> list[dict]:
    """
    Convert AI SDK request body to Strands Agent message history format.

    This extracts all messages EXCEPT the last one (which is the current user input)
    and converts them to the format expected by Strands Agent.

    The Strands Agent uses the same message format as Bedrock Converse API:
    - role: "user" or "assistant"
    - content: list of content blocks [{"text": "..."}, ...]

    Args:
        request_body: The parsed request body from the AI SDK frontend.

    Returns:
        list[dict]: List of messages in Strands Agent format, excluding the last message.
    """
    messages = []

    # Process all messages except the last one (current user input)
    for message in request_body.messages[:-1]:
        # Skip reasoning parts - only include text parts
        text_parts = []
        for part in message.parts:
            if part.type == vercel_ai_sdk_mate.MessagePartTypeEnum.TEXT.value:
                text_parts.append({"text": part.text})
            # Skip 'reasoning' type parts - agent doesn't need to see its previous thinking

        if text_parts:
            agent_message = {
                "role": message.role,
                "content": text_parts,
            }
            messages.append(agent_message)

    return messages


async def debug_ai_sdk_request(request: Request) -> dict:
    """
    Debug: Log incoming request for troubleshooting
    """
    debug("====== Incoming request")
    debug("------ Request Headers")
    for key, value in request.headers.items():
        debug(f"{key}: {value}")
    debug("------ Request Body")
    request_body_data = await request.json()
    request_body_formatted = json.dumps(request_body_data, indent=2, ensure_ascii=False)
    debug(request_body_formatted)
    sys.stderr.flush()
    return request_body_data


def ai_sdk_message_generator(output_text: str):
    """
    Stream response using AI SDK v5 Data Stream Protocol
    SSE format: each line starts with "data: " followed by JSON payload.
    Text streaming uses a three-phase pattern: start -> delta(s) -> end
    """
    message_id = str(uuid.uuid4())  # Unique ID for this text block

    # Phase 1: Signal that a new text block is starting
    yield f'data: {json.dumps({"type": "text-start", "id": message_id})}\n\n'

    # Phase 2: Send the actual text content (can be split into multiple deltas)
    yield f'data: {json.dumps({"type": "text-delta", "id": message_id, "delta": output_text})}\n\n'

    # Phase 3: Signal that the text block is complete
    yield f'data: {json.dumps({"type": "text-end", "id": message_id})}\n\n'

    # Signal that the entire message generation is finished
    yield f'data: {json.dumps({"type": "finish-message", "finishReason": "stop"})}\n\n'

    # SSE stream termination marker
    yield "data: [DONE]\n\n"


def ai_sdk_message_with_reasoning_generator(reasoning_text: str, output_text: str):
    """
    Stream response with both reasoning (thinking) and text using AI SDK v5 Data Stream Protocol.

    This function sends reasoning content first (shown as thinking/reasoning in the UI),
    then sends the main response text.

    SSE format: each line starts with "data: " followed by JSON payload.

    Events order:
    1. reasoning-start -> reasoning-delta -> reasoning-end (if reasoning_text is provided)
    2. text-start -> text-delta -> text-end
    3. finish-message
    """
    # Send reasoning/thinking content first (if provided)
    if reasoning_text:
        reasoning_id = str(uuid.uuid4())

        # Reasoning Phase 1: Signal that reasoning block is starting
        yield f'data: {json.dumps({"type": "reasoning-start", "id": reasoning_id})}\n\n'

        # Reasoning Phase 2: Send the reasoning content
        yield f'data: {json.dumps({"type": "reasoning-delta", "id": reasoning_id, "delta": reasoning_text})}\n\n'

        # Reasoning Phase 3: Signal that reasoning block is complete
        yield f'data: {json.dumps({"type": "reasoning-end", "id": reasoning_id})}\n\n'

    # Send main text response
    text_id = str(uuid.uuid4())

    # Text Phase 1: Signal that a new text block is starting
    yield f'data: {json.dumps({"type": "text-start", "id": text_id})}\n\n'

    # Text Phase 2: Send the actual text content
    yield f'data: {json.dumps({"type": "text-delta", "id": text_id, "delta": output_text})}\n\n'

    # Text Phase 3: Signal that the text block is complete
    yield f'data: {json.dumps({"type": "text-end", "id": text_id})}\n\n'

    # Signal that the entire message generation is finished
    yield f'data: {json.dumps({"type": "finish", "finishReason": "stop"})}\n\n'

    # SSE stream termination marker
    yield "data: [DONE]\n\n"
