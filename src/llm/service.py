"""Service layer: chains prompt building, LLM call, and parsing.

This is the entry point for generating interview questions.
The Streamlit UI calls `generate_interview_questions()` and gets back
a fully populated QuestionSet.

Change LLM provider? Only client.py changes.
Change prompt strategy? Only system_prompts.py changes.
Change parsing? Only parsing.py changes.
The UI is unaffected.
"""

from src.config.settings import Settings
from src.llm.client import LLMClient
from src.models.question import QuestionSet
from src.prompts.system_prompts import PROMPTS
from src.prompts.user_prompt import build_user_prompt
from src.utils.parsing import parse_question_set


def generate_interview_questions(
    settings: Settings,
    job_description: str,
    job_title: str,
    difficulty: str = "medium",
    num_questions: int = 5,
    prompt_variant: str = "few_shot",
    model: str | None = None,
) -> QuestionSet:
    """Generate interview questions for a job description.

    Chains: build user prompt → call LLM → parse response.

    Args:
        settings: Application settings.
        job_description: The job description text.
        job_title: A short title for the role (used in QuestionSet).
        difficulty: Difficulty level ('easy', 'medium', 'hard').
        num_questions: Number of questions to generate.
        prompt_variant: Which of the 5 system prompts to use.
        model: Optional model override.

    Returns:
        A fully populated QuestionSet.

    Raises:
        LLMAuthError, LLMRateLimitError, LLMConnectionError,
        LLMTruncatedError, LLMParseError, LLMError.
    """
    from src.models.question import Difficulty

    system_prompt = PROMPTS[prompt_variant]
    user_prompt = build_user_prompt(
        job_description=job_description,
        difficulty=Difficulty(difficulty),
        num_questions=num_questions,
    )

    client = LLMClient(settings=settings, model=model)
    raw = client.chat(system_prompt=system_prompt, user_prompt=user_prompt)

    if raw.content is None:
        from src.llm.exceptions import LLMParseError
        raise LLMParseError(
            "LLM returned empty content. Increase max_tokens.",
            raw_response=str(raw),
        )

    return parse_question_set(
        raw_text=raw.content,
        job_title=job_title,
        model_used=raw.model,
        prompt_variant=prompt_variant,
        usage=raw.usage,
    )
