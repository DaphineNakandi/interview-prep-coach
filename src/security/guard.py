"""LLM-based semantic security guard.

Uses a second LLM call to screen user input for malicious intent.
Runs only after the deterministic validator passes, so we don't
waste tokens on inputs that are already invalid.
"""

import json
import os
import re
from dataclasses import dataclass

from openai import OpenAI

from src.config.settings import Settings
from src.llm.exceptions import LLMError, LLMParseError
from src.security.prompt import GUARD_PROMPT

# Guard-specific model. Using the cheapest model because this is
# a binary classification task, not complex reasoning.
GUARD_MODEL = "openai/gpt-5-nano"


@dataclass
class GuardResult:
    """Result of the LLM security guard.

    Attributes:
        is_safe: True if the input is safe to process.
        category: One of 'safe', 'injection', 'abusive', 'off_topic'.
        reason: Brief explanation of the classification.
    """

    is_safe: bool
    category: str
    reason: str


def check_input_safety(text: str, settings: Settings) -> GuardResult:
    """Check if user input is safe to send to the main LLM.

    Uses a second LLM (cheap model) to classify the input.

    Args:
        text: The user input to check.
        settings: Application settings.

    Returns:
        GuardResult with is_safe, category, and reason.

    Raises:
        LLMError: If the guard LLM call fails (fail-closed — reject
            input if the guard can't verify it).
    """
    api_key = settings.openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
    client = OpenAI(
        base_url=settings.base_url,
        api_key=api_key,
    )

    try:
        response = client.chat.completions.create(
            model=GUARD_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": GUARD_PROMPT.format(user_input=text),
                }
            ],
            temperature=0.0,  # deterministic
            max_tokens=2000,
        )
    except Exception as e:
        # Fail-closed: if the guard fails, reject the input
        raise LLMError(f"Guard check failed: {e}") from e

    content = response.choices[0].message.content
    if content is None:
        raise LLMParseError(
            "Guard returned empty content.",
            raw_response=str(response),
        )



    # Strip markdown fences if present
    cleaned = re.sub(r"```(?:json)?\s*(.*?)\s*```", r"\1", content, flags=re.DOTALL).strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise LLMParseError(
            f"Guard returned invalid JSON: {e}",
            raw_response=content,
        ) from e

    return GuardResult(
        is_safe=bool(data.get("is_safe", False)),
        category=str(data.get("category", "unknown")),
        reason=str(data.get("reason", "")),
    )


