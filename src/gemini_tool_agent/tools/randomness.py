"""Random numbers and dice rolls."""

import json
import random

from gemini_tool_agent.tools.base import Tool


def random_number(min: int, max: int) -> str:
    """Return a random whole number between min and max (inclusive)."""
    # Parameter names shadow builtins on purpose: they must match the tool schema.
    return str(random.randint(min, max))


def roll_dice(sides: int = 6, count: int = 1) -> str:
    """Roll `count` dice with `sides` sides each."""
    if not (2 <= sides <= 1000 and 1 <= count <= 100):
        raise ValueError("sides must be 2-1000 and count must be 1-100")
    rolls = [random.randint(1, sides) for _ in range(count)]
    return json.dumps({"rolls": rolls, "total": sum(rolls)})


RANDOM_NUMBER = Tool(
    name="random_number",
    description="Generate a truly random whole number in a range. Use this whenever the "
    "user wants a random pick or number.",
    parameters={
        "type": "object",
        "properties": {
            "min": {"type": "integer", "description": "Lowest possible value"},
            "max": {"type": "integer", "description": "Highest possible value"},
        },
        "required": ["min", "max"],
    },
    func=random_number,
)

ROLL_DICE = Tool(
    name="roll_dice",
    description="Roll one or more dice and return each roll and the total.",
    parameters={
        "type": "object",
        "properties": {
            "sides": {"type": "integer", "description": "Sides per die (default 6)"},
            "count": {"type": "integer", "description": "Number of dice (default 1)"},
        },
    },
    func=roll_dice,
)
