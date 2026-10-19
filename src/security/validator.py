"""Deterministic input validation.

Fast, cheap checks that reject obviously invalid or malicious inputs
before the LLM guard runs (which is slower and costs tokens).
"""
MIN_INPUT_LENGTH = 50
MAX_INPUT_LENGTH = 5000

# Patterns that strongly suggest prompt injection or XSS.
# Conservative: only obvious injection phrases and XSS markers.
# The LLM guard catches subtle cases.

INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all previous",
    "forget your rules",
    "forget your instructions",
    "you are now",
    "disregard instructions",
    "disregard previous",
    "new instructions:",
    "<script",
    "</script>",
]


def validate_input(text: str) -> tuple[bool, str]:
    """Validate user input for length and obvious injection patterns.

    Args:
        text: The raw user input.

    Returns:
        A tuple (is_valid, message). If valid, message is a success
        message. If invalid, message explains why.
    """
    if not text or not text.strip():
        return False, "Input cannot be empty."

    if len(text) < MIN_INPUT_LENGTH:
        return (
            False,
            f"Job description too short. "
            f"Please provide at least {MIN_INPUT_LENGTH} characters.",
        )

    if len(text) > MAX_INPUT_LENGTH:
        return (
            False,
            f"Job description too long. "
            f"Please limit to {MAX_INPUT_LENGTH} characters.",
        )

    lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if pattern in lower:
            # Find the original casing for display
            idx = lower.find(pattern)
            original_match = text[idx:idx + len(pattern)]

            return (
                False,
                f"Input contains a suspicious pattern: '{original_match}'. "
                f"Please rephrase your job description.",
            )

    return True, "Input is valid."



