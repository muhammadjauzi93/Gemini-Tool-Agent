"""Terminal chat agent that answers with local Python tools via the Gemini Interactions API."""

from gemini_tool_agent.agent import Agent, ToolStepLimitError

__all__ = ["Agent", "ToolStepLimitError"]
__version__ = "0.1.0"
