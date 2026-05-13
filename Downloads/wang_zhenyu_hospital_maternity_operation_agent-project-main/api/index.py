# -*- coding: utf-8 -*-

"""
FastAPI backend for AI chat powered by Strands Agent.

This module provides the API endpoints that connect the frontend chat UI
to the Strands Agent with write operation capabilities. It implements the
Vercel AI SDK v5 Data Stream Protocol using Server-Sent Events (SSE).

Key components:
- /api/hello: Health check endpoint
- /api/chat: Main chat endpoint that processes messages and returns AI responses
  with both reasoning (thinking) and text content
"""

import os
import sys
import io
import asyncio

# fmt: off
from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse, StreamingResponse
from vercel_ai_sdk_mate.api import RequestBody  # Parses AI SDK request format

from labor_ward_ai.utils import debug
from labor_ward_ai.ai_sdk_adapter import debug_ai_sdk_request
from labor_ward_ai.ai_sdk_adapter import ai_sdk_message_with_reasoning_generator
from labor_ward_ai.ai_sdk_adapter import get_last_user_message_text
from labor_ward_ai.ai_sdk_adapter import request_body_to_agent_history
from labor_ward_ai.one.api import one  # Main singleton with agent
from labor_ward_ai.agent_debugger import extract_text_from_messages
from labor_ward_ai.agent_debugger import parse_response_text
from labor_ward_ai.quota import check_quota
from labor_ward_ai.quota import increment_usage
from labor_ward_ai.quota import QuotaExceededError
# fmt: on

# Add project root to sys.path for module imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

app = FastAPI()


@app.get("/api/hello")
async def hello_world():
    """
    Health check endpoint for testing FastAPI integration.

    Returns a simple JSON response to verify the API is running.
    """
    return JSONResponse(
        content={
            "message": "Hello from FastAPI!",
            "status": "success",
        },
    )


@app.post("/api/chat")
async def handle_chat_data(request: Request, protocol: str = Query("data")):
    """
    Main chat endpoint that processes user messages and returns AI responses.

    This endpoint uses the Strands Agent to process messages and returns
    responses with both reasoning (thinking) and text content using the
    Vercel AI SDK v5 Data Stream Protocol.

    The agent has access to database tools for:
    - Querying database schema and data
    - Assigning beds to patients
    - Creating medical orders
    - Creating alerts
    - Updating predictions

    Args:
        request: The incoming HTTP request containing chat messages
        protocol: Stream protocol version (default: "data" for AI SDK v5)
    """
    # --- Log incoming request for troubleshooting
    request_body_data = await debug_ai_sdk_request(request=request)

    # --- Parse the incoming request into AI SDK format
    request_body = RequestBody(**request_body_data)

    # --- Extract the last user message ---
    last_user_message = get_last_user_message_text(request_body)

    if not last_user_message:
        # Return error if no message found
        response = StreamingResponse(
            ai_sdk_message_with_reasoning_generator(
                reasoning_text="",
                output_text="Error: No message content found in request.",
            ),
            media_type="text/event-stream",
        )
        response.headers["x-vercel-ai-ui-message-stream"] = "v1"
        response.headers["Cache-Control"] = "no-cache"
        response.headers["Connection"] = "keep-alive"
        return response

    # --- Enforce monthly quota before spending tokens ---
    try:
        check_quota(one.bsm)
    except QuotaExceededError as e:
        debug(f"[Quota] blocked: {e}")
        response = StreamingResponse(
            ai_sdk_message_with_reasoning_generator(
                reasoning_text="",
                output_text=(
                    "Heads up — this is a personal demo, and I've set a "
                    "monthly token budget on it to keep my cloud bill from "
                    "going wild. We've hit that cap for this billing cycle, "
                    "so the chat is paused until the budget resets next "
                    "month. Thanks for trying it out!"
                ),
            ),
            media_type="text/event-stream",
        )
        response.headers["x-vercel-ai-ui-message-stream"] = "v1"
        response.headers["Cache-Control"] = "no-cache"
        response.headers["Connection"] = "keep-alive"
        return response

    # --- Get the agent and restore conversation history ---
    agent = one.agent

    # Clear previous messages and restore history from the frontend request.
    # The frontend sends all previous messages in request_body.messages.
    # We convert them to agent format and load them before processing the new message.
    agent.messages.clear()

    # Load conversation history (all messages except the last one, which is the current input)
    history_messages = request_body_to_agent_history(request_body)
    agent.messages.extend(history_messages)

    debug(f"[Agent] Loaded {len(history_messages)} history messages")

    # Record message count before calling agent (so we only extract new messages)
    msg_count_before = len(agent.messages)

    # Run agent in a thread pool to avoid blocking the async event loop.
    # The sync agent() call can take 10-30s (Bedrock API + tool use rounds),
    # and blocking the event loop would prevent FastAPI from maintaining the
    # TCP connection, causing proxy timeouts and "socket hang up" errors.
    def _run_agent():
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            return agent(last_user_message)
        finally:
            sys.stdout = old_stdout

    agent_result = await asyncio.to_thread(_run_agent)

    # --- Atomically record token spend for this invocation ---
    # NOTE: do NOT use metrics.accumulated_usage — strands accumulates that
    # across the lifetime of the Agent instance (and `one.agent` is cached),
    # so reading it would re-count every prior request. The per-invocation
    # total lives on the latest AgentInvocation, which strands appends at the
    # start of each agent() call.
    invocations = getattr(agent_result.metrics, "agent_invocations", None) or []
    usage = invocations[-1].usage if invocations else {}
    input_tokens = int(usage.get("inputTokens", 0) or 0)
    output_tokens = int(usage.get("outputTokens", 0) or 0)
    try:
        increment_usage(
            one.bsm,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
    except Exception as e:  # pragma: no cover - never let metering break a reply
        debug(f"[Quota] increment failed: {e}")

    # --- Extract thinking and answer from agent response ---
    full_text = extract_text_from_messages(agent.messages, msg_count_before)
    thinking, answer = parse_response_text(full_text)

    debug(f"[Agent] Thinking: {len(thinking)} chars")
    debug(f"[Agent] Answer: {len(answer)} chars")

    # --- Return SSE response with reasoning and text ---
    response = StreamingResponse(
        ai_sdk_message_with_reasoning_generator(
            reasoning_text=thinking,
            output_text=answer,
        ),
        media_type="text/event-stream",
    )
    response.headers["x-vercel-ai-ui-message-stream"] = "v1"
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    return response
