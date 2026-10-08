"""Exact word, character, and letter counts."""

import json

from gemini_tool_agent.tools.base import Tool


def count_text(text: str, letter: str = "") -> str:
    """Count words and characters, and optionally how often a letter appears."""
    counts = {
        "words": len(text.split()),
        "characters": len(text),
        "characters_without_spaces": len(text.replace(" ", "")),
    }
    if letter:
        counts[f"occurrences_of_{letter!r}"] = text.lower().count(letter.lower())
    return json.dumps(counts)


COUNT_TEXT = Tool(
    name="count_text",
    description="Count the exact number of words and characters in a text, and optionally "
    "how many times a letter appears. Use this for any counting question instead of "
    "counting yourself.",
    parameters={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "The text to analyse"},
            "letter": {
                "type": "string",
                "description": "Optional letter or substring to count (case-insensitive)",
            },
        },
        "required": ["text"],
    },
    func=count_text,
)
