"""Service layer: chains security, prompt building, LLM call, parsing.

This is the entry point for generating interview questions.
The Streamlit UI calls `generate_interview_questions()` and gets back
a fully populated QuestionSet.

Change LLM provider? Only client.py changes.
Change prompt strategy? Only system_prompts.py changes.
Change security rules? Only security/ module changes.
The UI is unaffected.
"""


from src.config.settings import Settings
from src.llm.client import LLMClient
from src.llm.exceptions import LLMParseError
from src.models.question import Difficulty, QuestionSet
from src.prompts.system_prompts import PROMPTS
from src.prompts.user_prompt import build_user_prompt
from src.security.exceptions import SecurityError
from src.security.guard import check_input_safety
from src.security.validator import validate_input
from src.utils.parsing import parse_question_set


def generate_interview_questions(
    settings: Settings,
    job_description: str,
    job_title: str,
    difficulty: str = "medium",
    num_questions: int = 5,
    prompt_variant: str = "few_shot",
    model: str | None = None,
    enable_llm_guard: bool = True,
) -> QuestionSet:
    """Generate interview questions for a job description.

    Pipeline: validate input → LLM guard → build prompt → call LLM → parse.

    Args:
        settings: Application settings.
        job_description: The job description text.
        job_title: A short title for the role (used in QuestionSet).
        difficulty: Difficulty level ('easy', 'medium', 'hard').
        num_questions: Number of questions to generate.
        prompt_variant: Which of the 5 system prompts to use.
        model: Optional model override.
        enable_llm_guard: If True, run the LLM-based guard. Disable
            for tests or when the deterministic validator is enough.

    Returns:
        A fully populated QuestionSet.

    Raises:
        SecurityError: If input fails validation or the LLM guard.
        LLMAuthError, LLMRateLimitError, LLMConnectionError,
        LLMTruncatedError, LLMParseError, LLMError.
    """
    # Layer 1: deterministic validation
    is_valid, message = validate_input(job_description)
    if not is_valid:
        raise SecurityError(f"Validation failed: {message}")

    # Layer 2: LLM guard (optional)
    if enable_llm_guard:
        guard_result = check_input_safety(job_description, settings)
        if not guard_result.is_safe:
            raise SecurityError(
                f"Input rejected ({guard_result.category}): "
                f"{guard_result.reason}"
            )

    # Build prompts
    system_prompt = PROMPTS[prompt_variant]
    user_prompt = build_user_prompt(
        job_description=job_description,
        difficulty=Difficulty(difficulty),
        num_questions=num_questions,
    )

    # Call the LLM
    client = LLMClient(settings=settings, model=model)
    raw = client.chat(system_prompt=system_prompt, user_prompt=user_prompt)

    if raw.content is None:
        raise LLMParseError(
            "LLM returned empty content. Increase max_tokens.",
            raw_response=str(raw),
        )

    # Parse and return
    return parse_question_set(
        raw_text=raw.content,
        job_title=job_title,
        model_used=raw.model,
        prompt_variant=prompt_variant,
        usage=raw.usage,
    )




