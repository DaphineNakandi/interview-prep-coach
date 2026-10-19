"""Custom exceptions for LLM operations.

All LLM-related errors inherit from LLMError so callers can catch
the whole family with one except clause, or specific types for
specific handling.
"""


class LLMError(Exception):
    """Base exception for all LLM-related errors."""


class LLMAuthError(LLMError):
    """Raised when the API key is invalid or missing."""


class LLMRateLimitError(LLMError):
    """Raised when the provider rate limit is hit."""


class LLMConnectionError(LLMError):
    """Raised when there's a network or connection issue."""


class LLMParseError(LLMError):
    """Raised when the LLM response cannot be parsed as valid JSON.

    Attributes:
        message: Human-readable error description.
        raw_response: The raw response from the LLM, preserved
            for debugging.
    """

    def __init__(self, message: str, raw_response: str) -> None:
        super().__init__(message)
        self.raw_response = raw_response


class LLMTruncatedError(LLMError):
    """Raised when the LLM response is truncated (finish_reason='length')."""


class LLMContentFilterError(LLMError):
    """Raised when the LLM output is blocked by a content filter."""



