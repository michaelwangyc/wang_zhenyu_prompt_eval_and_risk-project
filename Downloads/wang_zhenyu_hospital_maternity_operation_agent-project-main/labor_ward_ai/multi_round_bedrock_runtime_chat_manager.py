# -*- coding: utf-8 -*-

"""
Multi-round chat session manager for AWS Bedrock Runtime.

This module provides a high-level wrapper around the boto3 Bedrock Runtime
Converse API, making it easier to manage multi-turn conversations with AI models.

Key features:
- Manages conversation history automatically
- Converts raw API responses to typed dataclasses (via boto3_dataclass library)
- Provides convenient methods for sending text messages

Dependencies:
- boto3_dataclass: https://github.com/MacHu-GWU/boto3_dataclass-project
  Converts boto3 dictionary responses into typed dataclass objects,
  enabling IDE autocompletion and type checking.
- func_args: Utility for handling optional parameters in function calls.
"""

import typing as T
import sys
import dataclasses

from func_args.api import (
    OPT,
    remove_optional,
)  # OPT marks optional fields, remove_optional strips them
import boto3_dataclass_bedrock_runtime  # Typed dataclass wrappers for Bedrock responses

from rich import print as rprint  # Pretty printing for debugging

from .utils import debug

if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_bedrock_runtime import Client
    from mypy_boto3_bedrock_runtime.type_defs import (
        SystemContentBlockTypeDef,  # Type for system prompt blocks
        MessageUnionTypeDef,  # Type for user/assistant message blocks
    )
    from boto3_dataclass_bedrock_runtime.type_defs import (
        ConverseResponse,  # Typed response from converse() API
    )


@dataclasses.dataclass
class ChatSession:
    """
    Manages a multi-turn chat session with AWS Bedrock.

    This class wraps the Bedrock Converse API to provide:
    - Automatic conversation history management
    - Typed responses via boto3_dataclass
    - Simple interface for sending messages

    Attributes:
        client: The boto3 Bedrock Runtime client instance.
        model_id: The Bedrock model ID (e.g., "us.amazon.nova-micro-v1:0").
        system: Optional system prompt blocks that define AI behavior.

    Example:
        >>> session = ChatSession(
        ...     client=bedrock_runtime_client,
        ...     model_id="us.amazon.nova-micro-v1:0",
        ...     system=[{"text": "You are a helpful assistant."}],
        ... )
        >>> response = session.send_text_message("Hello!")
        >>> print(response.output.message.content[0].text)
    """

    # Required: boto3 Bedrock Runtime client
    client: "Client" = dataclasses.field()
    # Required: Model ID to use for inference
    model_id: str = dataclasses.field()
    # Optional: System prompt defining AI behavior and context
    system: T.Sequence["SystemContentBlockTypeDef"] = dataclasses.field(default=OPT)

    # Internal: Unique session identifier (can be overwritten for session continuity)
    _session_id: str = dataclasses.field(init=False)
    # Internal: Accumulated conversation history (user + assistant messages)
    _messages: list["MessageUnionTypeDef"] = dataclasses.field(init=False)

    def __post_init__(self):
        """Initialize internal state after dataclass construction."""
        self._session_id = "abc"  # Default session ID, typically overwritten
        self._messages = []  # Start with empty conversation history

    def send_message(
        self,
        messages: T.Sequence["MessageUnionTypeDef"],
    ) -> "ConverseResponse":
        """
        Send message(s) to the AI and get a response.

        This method:
        1. Appends new messages to conversation history
        2. Calls the Bedrock Converse API with full history
        3. Appends the AI's response to history for future turns
        4. Returns a typed response object

        Args:
            messages: List of message blocks to send. Each message should have
                      'role' ('user' or 'assistant') and 'content' fields.

        Returns:
            ConverseResponse: Typed response with output text, usage stats, etc.
                             Access the response text via: response.output.message.content[0].text
        """
        print("===== Send message")

        # Append new messages to conversation history
        self._messages.extend(messages)

        # Build API request parameters
        kwargs = dict(
            modelId=self.model_id,
            messages=self._messages,  # Full conversation history
            system=self.system,  # System prompt (if any)
        )
        kwargs = remove_optional(**kwargs)  # Strip None/OPT values

        # Debug: Print outgoing request
        print("----- Converse kwargs:")
        rprint(kwargs)

        # Call Bedrock Converse API
        response = self.client.converse(**kwargs)

        # Convert raw dict response to typed dataclass for better IDE support
        response = boto3_dataclass_bedrock_runtime.caster.converse(response)

        # Debug: Print response (excluding metadata noise)
        print("----- Converse response:")
        del response.boto3_raw_data["ResponseMetadata"]
        rprint(response.boto3_raw_data)

        # Append AI's response to history for multi-turn context
        self._messages.append(response.output.message.boto3_raw_data)

        return response

    def send_text_message(
        self,
        message: str,
    ) -> "ConverseResponse":
        """
        Convenience method to send a simple text message.

        Wraps the message string in the required Bedrock message format
        and calls send_message().

        Args:
            message: Plain text message from the user.

        Returns:
            ConverseResponse: The AI's response.
        """
        return self.send_message(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": message,
                        },
                    ],
                }
            ],
        )

    def debug_response(self, response: "ConverseResponse") -> str:
        """
        Log response for debugging.
        """
        debug("------ Chat response")
        output_text = response.output.message.content[0].text
        debug(output_text)
        debug("------ Token Usage")
        debug(str(response.usage))
        sys.stderr.flush()
        return output_text
