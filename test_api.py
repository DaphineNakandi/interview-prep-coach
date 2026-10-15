"""Temporary script to verify OpenRouter API key works."""

from openai import OpenAI

from src.config.settings import load_settings

settings = load_settings()

if not settings.is_configured:
    print("ERROR: API key not set")
    exit(1)

client = OpenAI(
    base_url=settings.base_url,
    api_key=settings.openrouter_api_key,
)

try:
    response = client.chat.completions.create(
        model=settings.default_model,
        messages=[{"role": "user", "content": "Say 'API works' in 3 words."}],
        max_tokens=20,
    )
    print("SUCCESS:", response.choices[0].message.content)
    print("Model:", response.model)
    print("Tokens used:", response.usage.total_tokens)
except Exception as e:
    print(f"FAILED: {type(e).__name__}: {e}")

