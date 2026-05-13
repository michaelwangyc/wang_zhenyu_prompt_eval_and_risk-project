# -*- coding: utf-8 -*-

"""
LLM output post-processing utilities.

Reusable helpers for cleaning and extracting structured data from raw LLM
text responses.
"""

import json
import re
import typing as T

from .exc import JsonExtractionError


def extract_json(text: str) -> T.Any:
    """Extract and parse a single JSON object from raw LLM response text.

    Assumes the LLM output contains exactly **one** JSON value — either
    bare or wrapped in a single markdown code fence (````` ```json … ``` `````
    or ````` ``` … ``` `````).  If a code fence is present, only its content
    is parsed; any text outside the fence is ignored.  If no fence is found,
    the entire *text* is treated as JSON.

    This function does **not** handle multiple JSON values in a single
    response.  If the LLM returns more than one JSON block, only the first
    fenced block (or the full text when unfenced) is considered.

    Parameters
    ----------
    text:
        Raw LLM response text, potentially wrapped in markdown code fences.

    Returns
    -------
    Any
        The parsed JSON value (typically a ``dict`` or ``list``).

    Raises
    ------
    JsonExtractionError
        If the extracted text is not valid JSON.  The exception carries the
        full raw LLM output (``raw_output`` attribute) and the original
        parse error as ``__cause__`` for downstream inspection.
    """
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    raw = match.group(1) if match else text

    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        raise JsonExtractionError(raw_output=text, cause=exc) from exc
