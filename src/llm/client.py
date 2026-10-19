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

    Attributes:
        settings: Application settings.
        model: The model slug to use for generation.
        client: The underlying OpenAI SDK client.
    """

    def __init__(self, settings: Settings, model: str | None = None) -> None:
        """Initialize the client.

        Args:
            settings: Application settings with API key and base URL.
            model: Optional model override. If None, uses
                settings.default_model.
        """
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
        """Send a chat completion request and return the raw response.

        Args:
            system_prompt: The system message (persona, rules, format).
            user_prompt: The user message (job-specific details).
            temperature: Sampling temperature. If None, uses
                settings.default_temperature.
            max_tokens: Max tokens for the response. If None, uses
                settings.default_max_tokens.

        Returns:
            RawResponse with content, model, finish_reason, and usage.

        Raises:
            LLMAuthError: If the API key is invalid.
            LLMRateLimitError: If the provider rate limit is hit.
            LLMConnectionError: If there's a network issue.
            LLMTruncatedError: If the response was truncated.
            LLMError: For other API errors.
        """
        temperature = (
            temperature if temperature is not None
            else self.settings.default_temperature
        )
        max_tokens = (
            max_tokens if max_tokens is not None
            else self.settings.default_max_tokens
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


