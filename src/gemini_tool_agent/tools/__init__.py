"""Tool registry. To add a tool, create a module with a `Tool` and list it in ALL_TOOLS."""

from gemini_tool_agent.tools.base import Tool
from gemini_tool_agent.tools.calculator import CALCULATE
from gemini_tool_agent.tools.clock import GET_CURRENT_DATETIME
from gemini_tool_agent.tools.randomness import RANDOM_NUMBER, ROLL_DICE
from gemini_tool_agent.tools.text import COUNT_TEXT
from gemini_tool_agent.tools.units import CONVERT_UNITS

ALL_TOOLS: list[Tool] = [
    CALCULATE,
    GET_CURRENT_DATETIME,
    CONVERT_UNITS,
    RANDOM_NUMBER,
    ROLL_DICE,
    COUNT_TEXT,
]

__all__ = ["ALL_TOOLS", "Tool"]
