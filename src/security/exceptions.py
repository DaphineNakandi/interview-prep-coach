"""Security-related exceptions."""

from src.llm.exceptions import LLMError


class SecurityError(LLMError):
    """Raised when input fails security checks."""


