"""Settings loaded from environment variables and the .env file."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

DEFAULT_MODEL = "gemini-3.8-flash"
DEFAULT_MAX_TOOL_STEPS = 10


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    model: str = DEFAULT_MODEL
    max_tool_steps: int = DEFAULT_MAX_TOOL_STEPS
    show_tool_calls: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from the environment. Variables already set in the shell win over .env."""
        load_dotenv()

        # genai.Client() reads either variable; GOOGLE_API_KEY takes priority in the SDK.
        if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
            raise ConfigError("No API key found. Set GEMINI_API_KEY in .env (see .env.example).")

        max_steps = os.getenv("MAX_TOOL_STEPS", str(DEFAULT_MAX_TOOL_STEPS))
        if not max_steps.isdigit() or int(max_steps) < 1:
            raise ConfigError(f"MAX_TOOL_STEPS must be a positive integer, got {max_steps!r}")

        return cls(
            model=os.getenv("GEMINI_MODEL") or DEFAULT_MODEL,
            max_tool_steps=int(max_steps),
            show_tool_calls=os.getenv("SHOW_TOOL_CALLS", "true").strip().lower()
            in ("1", "true", "yes", "on"),
        )
