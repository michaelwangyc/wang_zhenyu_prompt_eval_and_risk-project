# -*- coding: utf-8 -*-

"""
Custom exceptions for the prompt_risk package.
"""


class JsonExtractionError(Exception):
    """Failed to extract valid JSON from LLM output text.

    Raised when :func:`prompt_risk.llm_output.extract_json` cannot parse
    the LLM response into a JSON object.  The error message includes a
    truncated preview of the raw LLM output to aid debugging.

    Attributes
    ----------
    raw_output : str
        The full, unmodified LLM output text that failed extraction.
    """

    def __init__(self, raw_output: str, cause: Exception) -> None:
        self.raw_output = raw_output
        preview = raw_output[:200] + ("..." if len(raw_output) > 200 else "")
        super().__init__(
            f"Failed to extract JSON from LLM output: {cause}\n"
            f"--- LLM output (preview) ---\n{preview}"
        )
        self.__cause__ = cause
