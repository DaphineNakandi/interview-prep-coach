"""Parsing utilities for LLM responses.

The LLM may return JSON in different forms:
- Plain JSON object
- Markdown-wrapped JSON (```json ... ```)
- Malformed JSON

This module handles all cases and returns typed objects.
"""

import json
import re
from datetime import UTC

from src.llm.exceptions import LLMParseError
from src.models.question import Difficulty, Question, QuestionSet, Usage


def _strip_markdown_json(text: str) -> str:
    """Remove markdown code fences around JSON if present.

    Args:
        text: Raw LLM output, possibly wrapped in ```json ... ```.

    Returns:
        The JSON string without markdown fences.
    """
    match = re.search(
        r"```(?:json)?\s*(.*?)\s*```",
        text,
        re.DOTALL,
    )
    if match:
        return match.group(1)
    return text.strip()


def parse_question_set(
    raw_text: str,
    job_title: str,
    model_used: str,
    prompt_variant: str,
    usage: Usage | None = None,
) -> QuestionSet:
    """Parse raw LLM output into a QuestionSet.

    Args:
        raw_text: The raw content from the LLM.
        job_title: The role the questions are for.
        model_used: The model that generated the response.
        prompt_variant: Which system prompt variant was used.
        usage: Optional usage data to attach.

    Returns:
        A parsed QuestionSet.

    Raises:
        LLMParseError: If the response cannot be parsed or doesn't match
            the expected schema.
    """
    cleaned = _strip_markdown_json(raw_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise LLMParseError(
            f"Failed to parse JSON: {e}",
            raw_response=raw_text,
        ) from e

    # Some prompts return {"questions": [...]}, others return [...]
    if isinstance(data, dict) and "questions" in data:
        items = data["questions"]
    elif isinstance(data, list):
        items = data
    else:
        raise LLMParseError(
            "Response is neither a list nor an object with 'questions'.",
            raw_response=raw_text,
        )

    questions: list[Question] = []
    for i, item in enumerate(items, start=1):
        try:
            questions.append(
                Question(
                    id=item.get("id", i),
                    question=item["question"],
                    reference_answer=item["reference_answer"],
                    category=item.get("category", "general"),
                    difficulty=Difficulty(item.get("difficulty", "medium")),
                    skills_tested=item.get("skills_tested", []),
                    follow_up=item.get("follow_up", ""),
                )
            )
        except (KeyError, ValueError) as e:
            raise LLMParseError(
                f"Question {i} has invalid schema: {e}",
                raw_response=raw_text,
            ) from e

    from datetime import datetime
    return QuestionSet(
        questions=questions,
        job_title=job_title,
        generated_at=datetime.now(UTC).isoformat(),
        model_used=model_used,
        prompt_variant=prompt_variant,
        usage=usage,
    )



