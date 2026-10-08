"""Interactive terminal interface."""

import sys
from typing import Any

from google import genai
from google.genai import errors

from gemini_tool_agent.agent import Agent, ToolStepLimitError
from gemini_tool_agent.config import ConfigError, Settings
from gemini_tool_agent.tools import ALL_TOOLS

EXIT_COMMANDS = ("exit", "quit")
RESET_COMMAND = "/reset"


def print_tool_call(name: str, arguments: dict[str, Any], result: str, is_error: bool) -> None:
    print(f"  [tool] {name}({arguments})")
    print(f"  [tool] -> {result}")


def main() -> int:
    try:
        settings = Settings.from_env()
    except ConfigError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    agent = Agent(
        client=genai.Client(),
        tools=ALL_TOOLS,
        model=settings.model,
        max_tool_steps=settings.max_tool_steps,
        on_tool_call=print_tool_call if settings.show_tool_calls else None,
    )

    print(f"Gemini Tool Agent ({settings.model}). Type '/reset' for a new chat, 'exit' to quit.")

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if user_input.lower() in EXIT_COMMANDS:
            return 0
        if user_input.lower() == RESET_COMMAND:
            agent.reset()
            print("Started a new conversation.")
            continue
        if not user_input:
            continue

        try:
            reply = agent.send(user_input)
        except ToolStepLimitError as e:
            print(f"  [agent] {e}")
            continue
        except errors.APIError as e:
            print(f"API error: {e}", file=sys.stderr)
            continue

        print(f"AI: {reply}")


if __name__ == "__main__":
    raise SystemExit(main())
