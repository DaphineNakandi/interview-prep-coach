"""Application configuration.
Loads environment variables from .env and provides a Settings dataclass
that other modules import. No hardcoded values elsewhere in the codebase.

"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load .env file at import time.
# This must happen before os.getenv() calls below.
from  pathlib import Path

# Force load the .env file from the root of the project
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)


# Defaults
# Code-level defaults. Overridable via .env.
# Having these here means the app works out of the box

DEFAULT_MODEL = "openai/gpt-5-mini"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 4000
DEFAULT_NUM_QUESTIONS = 5
DEFAULT_DIFFICULTY = "medium"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
APP_TITLE = "Interview Prep Coach"

@dataclass
class Settings:
    """Application Settings

    Attributes:
        openrouter_api_key (str): API key for OpenRouter. None if not set.
        default_model: Model slug to use for generation.
        default_temperature: Sampling temperature (0.0 to 1.0).
        default_max_tokens: Maximum tokens in the LLM response.
        default_num_questions: Default number of questions to generate.
        default_difficulty: Default difficulty level for questions.
        base_url: OpenRouter API base URL.
        app_title: Title displayed in the Streamlit UI.

    """

    openrouter_api_key: str | None
    default_model: str
    default_temperature: float
    default_max_tokens: int
    default_num_questions: int
    default_difficulty: str
    base_url: str
    app_title: str

    @property
    def is_configured(self) -> bool:
        """ Check if the app has the required configuration.

        Returns:
        True if OPENROUTER_API_KEY is set, False otherwise.

        """
        return self.openrouter_api_key is not None

def load_settings() -> Settings:
    """Load settings from environment variables with sensible defaults.

    Environment variables are read from .env (loaded at import time).
    MIssing values fall back to module-level defaults, except for the
    API key, which is None if missing.

    Returns:
        A Settings instance populated from environment variables.
    """
    return Settings(
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        default_model=os.getenv("DEFAULT_MODEL", "DEFAULT_MODEL"),
        default_temperature=float(
            os.getenv("DEFAULT_TEMPERATURE", str(DEFAULT_TEMPERATURE))
        ),
        default_max_tokens=int(
            os.getenv("DEFAULT_MAX-TOKENS", str(DEFAULT_MAX_TOKENS))
        ),
        default_num_questions=int(
            os.getenv("DEFAULT_NUM_QUESTIONS", str(DEFAULT_NUM_QUESTIONS))
        ),
        default_difficulty=os.getenv("DEFAULT_DIFFICULTY", DEFAULT_DIFFICULTY),
        base_url=os.getenv("OPENROUTER_BASE_URL", OPENROUTER_BASE_URL),
        app_title=os.getenv("APP_TITLE", APP_TITLE),
    )















