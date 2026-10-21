"""LLM client for OpenRouter.

Wraps the OpenAI SDK to provide a clean interface for calling
the LLM. Returns RawResponse — parsing happens in a separate module.

Callers should not import from `openai` directly. This module is the
only place that touches the SDK.
"""

from openai import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)

from src.config.settings import Settings
from src.llm.exceptions import (
    LLMAuthError,
    LLMConnectionError,
    LLMError,
    LLMRateLimitError,
    LLMTruncatedError,
)
from src.models.question import RawResponse, Usage


class LLMClient:
    """Client for calling OpenRouter via the OpenAI SDK.

    Holds config (API key, base URL, model) and the SDK client instance.
    Instantiate once, reuse across calls.
    """

    def __init__(self, settings: Settings, model: str | None = None) -> None:
        """Initialize the client."""
        if not settings.is_configured:
            raise LLMAuthError(
                "OPENROUTER_API_KEY is not set. Add it to your .env file."
            )

        self.settings = settings
        self.model = model or settings.default_model
        self.client = OpenAI(
            base_url=settings.base_url,
            api_key=settings.openrouter_api_key,
        )

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> RawResponse:
        """Send a chat completion request and return the raw response."""
        temperature = (
            temperature
            if temperature is not None
            else self.settings.default_temperature
        )
        max_tokens = (
            max_tokens if max_tokens is not None else self.settings.default_max_tokens
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except AuthenticationError as e:
            raise LLMAuthError(
                f"Authentication failed. Check your OPENROUTER_API_KEY. ({e})"
            ) from e
        except RateLimitError as e:
            raise LLMRateLimitError(
                f"Rate limited. Wait a moment and try again. ({e})"
            ) from e
        except APIConnectionError as e:
            raise LLMConnectionError(
                f"Network error. Check your connection. ({e})"
            ) from e
        except APIError as e:
            raise LLMError(f"API error: {e}") from e

        choice = response.choices[0]
        usage_data = response.usage

        usage = Usage(
            prompt_tokens=usage_data.prompt_tokens,
            completion_tokens=usage_data.completion_tokens,
            total_tokens=usage_data.total_tokens,
            cost_usd=getattr(usage_data, "cost", 0.0) or 0.0,
            reasoning_tokens=(
                getattr(
                    usage_data.completion_tokens_details,
                    "reasoning_tokens",
                    0,
                )
                or 0
            ),
        )

        if choice.finish_reason == "length":
            raise LLMTruncatedError(
                f"Response was truncated at {max_tokens} tokens. "
                f"Increase max_tokens or reduce the prompt size."
            )
        if choice.finish_reason == "content_filter":
            raise LLMError(
                "Response was blocked by a content filter. "
                "Try rephrasing your input."
            )

        return RawResponse(
            content=choice.message.content,
            model=response.model,
            finish_reason=choice.finish_reason or "unknown",
            usage=usage,
        )

    def evaluate_answer(
        self,
        question: str,
        reference_answer: str,
        user_answer: str,
        prompt_variant: str = "few_shot",
    ) -> str:
        """Evaluate a user's answer against a reference answer.

        Adapts the feedback style based on the selected prompt technique.
        """
        # Base persona
        base_prompt = (
            "You are an expert technical interviewer. Your job is to evaluate "
            "a candidate's answer to an interview question."
        )

        # Adapt the evaluation style based on the prompt variant
        if prompt_variant == "chain_of_thought":
            style_prompt = (
                "Evaluate the candidate's answer by breaking down their logic step-by-step. "
                "First analyze what they did well, then trace their logic to identify "
                "what they missed or where they could improve."
            )
        elif prompt_variant == "zero_shot":
            style_prompt = (
                "Provide a direct, concise evaluation of the candidate's answer. "
                "Highlight what was good and what was missing."
            )
        elif prompt_variant == "role_based":
            style_prompt = (
                "Evaluate the candidate's answer as a strict but fair senior hiring manager. "
                "Be demanding but constructive in your feedback."
            )
        elif prompt_variant == "structured_output":
            style_prompt = (
                "Evaluate the candidate's answer by organizing your feedback into "
                "two clear sections: 'Strengths' and 'Areas for Improvement'."
            )
        else:  # Default (few_shot)
            style_prompt = (
                "Provide constructive feedback comparing their answer to the reference answer. "
                "Highlight what they did well and what they missed."
            )

        system_prompt = f"{base_prompt} {style_prompt} Keep your feedback under 150 words."

        user_prompt = (
            f"Question: {question}\n\n"
            f"Reference Answer: {reference_answer}\n\n"
            f"Candidate's Answer: {user_answer}\n\n"
            "Provide your evaluation:"
        )

        # We reuse the chat method, but we don't need JSON parsing here.
        raw = self.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            max_tokens=1500,
        )
        return raw.content or "Could not evaluate answer."


