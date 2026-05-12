# -*- coding: utf-8 -*-

"""
Agent debugging utilities.

This module provides helper functions for debugging agent responses,
extracting thinking process, and formatting multi-turn conversations.

Usage:
    from labor_ward_ai.one.one_05_agent_debugger import chat, print_summary

    agent = one.agent
    agent.messages.clear()

    thinking, answer = chat(agent, "Your question here", turn_number=1)
"""

import io
import re
import sys

from strands import Agent


def extract_text_from_messages(
    messages: list,
    start_index: int = 0,
    debug: bool = False,
) -> str:
    """
    Extract <thinking> tags from ALL assistant messages, but other text only from the LAST one.

    Strands Agent embeds thinking content as <thinking>...</thinking> tags directly in the
    text field of each assistant message. When an agent calls multiple tools, it produces
    multiple assistant messages, each with its own thinking block.

    To get the complete reasoning chain:
    - Collect <thinking> content from ALL assistant messages
    - Only take non-thinking text from the LAST assistant message (final answer)

    Args:
        messages: List of message dicts from agent.messages
        start_index: Index to start looking from (use msg_count_before)
        debug: If True, print message structure for debugging

    Returns:
        str: All thinking content wrapped in a single <thinking> tag, followed by
             the final text response.

    Example:
        msg_count_before = len(agent.messages)
        agent("Your question")
        full_text = extract_text_from_messages(agent.messages, msg_count_before)
    """
    thinking_pattern = r"<thinking>(.*?)</thinking>"

    # Collect ALL thinking content from all assistant messages
    all_thinking = []
    # Track the last assistant message for final text
    last_assistant_text = None

    for i, msg in enumerate(messages[start_index:], start=start_index):
        if debug:
            print(f"\n[DEBUG] Message {i}:")
            print(f"  role: {msg.get('role')}")
            content = msg.get("content", [])
            print(f"  content type: {type(content)}")
            if isinstance(content, list):
                for j, item in enumerate(content):
                    if isinstance(item, dict):
                        print(f"    [{j}] keys: {list(item.keys())}")
                    else:
                        print(f"    [{j}] type: {type(item)}")

        if msg.get("role") == "assistant":
            content = msg.get("content", [])
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    text = item["text"]

                    # Extract <thinking> content from this message
                    thinking_matches = re.findall(thinking_pattern, text, re.DOTALL)
                    for match in thinking_matches:
                        if match.strip():
                            all_thinking.append(match.strip())

                    # Keep track of the last assistant's text (will use for final answer)
                    last_assistant_text = text

    if debug:
        print(f"\n[DEBUG] Collected {len(all_thinking)} thinking blocks from all messages")

    # Build final result
    texts = []

    # Add all thinking wrapped in a single <thinking> tag
    if all_thinking:
        combined_thinking = "\n\n".join(all_thinking)
        texts.append(f"<thinking>{combined_thinking}</thinking>")

    # Add text from the LAST assistant message, but remove its <thinking> tags
    # (since we already collected all thinking above)
    if last_assistant_text:
        final_answer = re.sub(thinking_pattern, "", last_assistant_text, flags=re.DOTALL)
        final_answer = final_answer.strip()
        if final_answer:
            texts.append(final_answer)

    return "\n".join(texts)


def parse_response_text(
    full_text: str,
) -> tuple[str, str]:
    """
    Parse full response text into thinking process and final answer.

    This function separates the agent's thinking (reasoning) from its
    final answer by extracting <thinking> tags.

    Args:
        full_text: Full text including <thinking> tags

    Returns:
        tuple[str, str]: (thinking_process, final_answer)
            - thinking_process: All thinking blocks concatenated
            - final_answer: The response with thinking blocks removed

    Example:
        full_text = "<thinking>Let me analyze...</thinking>The answer is 42."
        thinking, answer = parse_response_text(full_text)
        # thinking = "Let me analyze..."
        # answer = "The answer is 42."
    """
    # Extract all <thinking>...</thinking> blocks
    thinking_pattern = r"<thinking>(.*?)</thinking>"
    thinking_matches = re.findall(thinking_pattern, full_text, re.DOTALL)
    thinking_process = "\n\n".join(match.strip() for match in thinking_matches)

    # Remove <thinking> blocks to get final answer
    final_answer = re.sub(thinking_pattern, "", full_text, flags=re.DOTALL)

    # Clean up orphaned markdown headers (e.g., "## " or "### " with nothing after)
    # These appear when agent streams responses in chunks
    final_answer = re.sub(r"^#{1,6}\s*$", "", final_answer, flags=re.MULTILINE)

    # Clean up multiple newlines
    final_answer = re.sub(r"\n{3,}", "\n\n", final_answer)

    # Strip leading/trailing whitespace
    final_answer = final_answer.strip()

    return thinking_process, final_answer


def chat(
    agent: Agent,
    message: str,
    turn_number: int = 1,
    verbose: bool = False,
    debug: bool = False,
) -> tuple[str, str]:
    """
    Send a message to the agent and return parsed response.

    This is the main debugging function for multi-turn conversations.
    It handles:
    - Printing formatted turn headers and request
    - Suppressing/showing streaming output
    - Extracting and parsing the response
    - Separating thinking from final answer

    Args:
        agent: The strands Agent instance
        message: User message to send
        turn_number: Turn number for display (default: 1)
        verbose: If True, print raw streaming output; if False, suppress it
        debug: If True, print message structure for debugging

    Returns:
        tuple[str, str]: (thinking_process, final_answer)

    Example:
        from labor_ward_ai.one.api import one
        from labor_ward_ai.one.one_05_agent_debugger import chat

        agent = one.agent
        agent.messages.clear()

        # Turn 1
        thinking, answer = chat(agent, "Find patients in labor", turn_number=1)
        results.append(("Query", thinking, answer))

        # Turn 2 (conversation continues)
        thinking, answer = chat(agent, "Transfer the first patient", turn_number=2)
        results.append(("Execute", thinking, answer))
    """
    # Print turn header
    print("=" * 70)
    print(f"  TURN {turn_number}")
    print("=" * 70)

    # Print request
    print("\n[REQUEST]")
    print("-" * 70)
    print(message)

    # Record message count before calling agent
    msg_count_before = len(agent.messages)

    # Call agent (this prints streaming output)
    if verbose:
        result = agent(message)
    else:
        # Suppress streaming output by redirecting stdout temporarily
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            result = agent(message)
        finally:
            sys.stdout = old_stdout

    # Extract full text from new messages (debug=True to see message structure)
    full_text = extract_text_from_messages(
        agent.messages, msg_count_before, debug=debug
    )

    # Parse into thinking and answer
    thinking, answer = parse_response_text(full_text)

    # Print thinking (if any)
    if thinking:
        print("\n[THINKING]")
        print("-" * 70)
        print(thinking)

    # Print final answer
    print("\n[RESPONSE]")
    print("-" * 70)
    print(answer)

    print("\n")  # Extra spacing between turns

    return thinking, answer


def print_summary(results: list[tuple[str, str, str]]) -> None:
    """
    Print summary of test results.

    Args:
        results: List of tuples (turn_name, thinking, answer)

    Example:
        results = []
        results.append(("Query", thinking1, answer1))
        results.append(("Execute", thinking2, answer2))
        results.append(("Verify", thinking3, answer3))
        print_summary(results)
    """
    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    for turn_name, thinking, answer in results:
        print(f"\n[{turn_name}]")
        print(f"  Thinking: {len(thinking)} chars")
        print(f"  Answer: {len(answer)} chars")


def print_multi_turn_conversation_headers(name: str, n_turns: int) -> None:
    print("\n")
    print("=" * 70)
    print(f"  TEST: {name} - Multi-turn conversation ({n_turns} turns)")
    print("=" * 70)
    print("\n")
