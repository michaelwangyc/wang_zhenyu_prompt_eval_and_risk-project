# -*- coding: utf-8 -*-

import pytest

from prompt_risk.exc import JsonExtractionError
from prompt_risk.llm_output import extract_json


class TestExtractJson:
    """Tests for extract_json()."""

    def test_plain_json(self):
        """Plain JSON without fences is parsed correctly."""
        assert extract_json('{"key": "value"}') == {"key": "value"}

    def test_json_code_fence(self):
        """```json ... ``` fences are stripped and parsed."""
        raw = '```json\n{"key": "value"}\n```'
        assert extract_json(raw) == {"key": "value"}

    def test_plain_code_fence(self):
        """``` ... ``` fences (without language tag) are stripped and parsed."""
        raw = '```\n{"key": "value"}\n```'
        assert extract_json(raw) == {"key": "value"}

    def test_surrounding_text_ignored(self):
        """Text before/after fences is discarded; only fenced content parsed."""
        raw = 'Here is the result:\n```json\n{"a": 1}\n```\nDone.'
        assert extract_json(raw) == {"a": 1}

    def test_multiline_json(self):
        """Multi-line JSON inside fences is parsed correctly."""
        raw = '```json\n{\n  "a": 1,\n  "b": [2, 3]\n}\n```'
        assert extract_json(raw) == {"a": 1, "b": [2, 3]}

    def test_whitespace_around_json(self):
        """Leading/trailing whitespace inside fences is tolerated."""
        raw = '```json\n  {"key": "value"}  \n```'
        assert extract_json(raw) == {"key": "value"}

    def test_nested_braces(self):
        """Nested JSON objects inside fences are handled correctly."""
        raw = '```json\n{"outer": {"inner": [1, 2, {"deep": true}]}}\n```'
        assert extract_json(raw) == {"outer": {"inner": [1, 2, {"deep": True}]}}

    def test_first_fence_wins(self):
        """When multiple fenced blocks exist, the first one is extracted."""
        raw = '```json\n{"first": 1}\n```\n\n```json\n{"second": 2}\n```'
        assert extract_json(raw) == {"first": 1}

    def test_json_list(self):
        """JSON arrays are parsed correctly."""
        assert extract_json("[1, 2, 3]") == [1, 2, 3]


class TestExtractJsonErrors:
    """Error cases — all should raise JsonExtractionError."""

    def test_plain_text_raises(self):
        """Non-JSON text raises JsonExtractionError."""
        with pytest.raises(JsonExtractionError) as exc_info:
            extract_json("This is not JSON at all.")
        assert exc_info.value.raw_output == "This is not JSON at all."
        assert exc_info.value.__cause__ is not None

    def test_empty_string_raises(self):
        """Empty string raises JsonExtractionError."""
        with pytest.raises(JsonExtractionError) as exc_info:
            extract_json("")
        assert exc_info.value.raw_output == ""

    def test_invalid_json_in_fence_raises(self):
        """Invalid JSON inside fences raises JsonExtractionError."""
        raw = "```json\n{bad json}\n```"
        with pytest.raises(JsonExtractionError) as exc_info:
            extract_json(raw)
        assert exc_info.value.raw_output == raw

    def test_error_message_contains_preview(self):
        """Error message includes a preview of the LLM output."""
        raw = "The model said something unexpected."
        with pytest.raises(JsonExtractionError, match="LLM output"):
            extract_json(raw)

    def test_long_output_is_truncated_in_message(self):
        """Preview in error message is truncated for long outputs."""
        raw = "x" * 500
        with pytest.raises(JsonExtractionError) as exc_info:
            extract_json(raw)
        msg = str(exc_info.value)
        assert "..." in msg
        # The 500-char raw output should be truncated to 200 in the preview.
        assert raw not in msg


if __name__ == "__main__":
    from prompt_risk.tests import run_cov_test

    run_cov_test(
        __file__,
        "prompt_risk.llm_output",
        preview=False,
    )
