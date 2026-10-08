"""The Tool type shared by every tool module."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Tool:
    """A Python function plus the description the model sees."""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema for the function's arguments
    func: Callable[..., str]

    def schema(self) -> dict[str, Any]:
        """Return the declaration sent to the Gemini API in `tools=`."""
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
