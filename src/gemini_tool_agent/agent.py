"""The agent: conversation memory plus the tool-calling loop."""

from collections.abc import Callable, Sequence
from typing import Any

from gemini_tool_agent.tools import Tool

# Called after each tool runs: (tool name, arguments, result, is_error).
ToolCallHook = Callable[[str, dict[str, Any], str, bool], None]


class ToolStepLimitError(RuntimeError):
    """Raised when the model keeps requesting tools past the step limit."""


class Agent:
    """Chats with a Gemini model and runs the local tools it asks for.

    The server stores each interaction; passing the previous ID gives the model
    the full conversation history without resending it.
    """

    def __init__(
        self,
        client: Any,
        tools: Sequence[Tool],
        model: str,
        max_tool_steps: int = 10,
        on_tool_call: ToolCallHook | None = None,
    ) -> None:
        self._client = client
        self._model = model
        self._max_tool_steps = max_tool_steps
        self._on_tool_call = on_tool_call
        self._tools = {tool.name: tool for tool in tools}
        self._schemas = [tool.schema() for tool in tools]
        self._previous_id: str | None = None

    def reset(self) -> None:
        """Start a new conversation."""
        self._previous_id = None

    def send(self, message: str) -> str:
        """Send a user message and return the model's final text reply."""
        interaction = self._create(message, self._previous_id)

        # Agent loop: run any tools the model asks for and send the results back,
        # until it replies with text.
        steps = 0
        while calls := self._function_calls(interaction):
            if steps >= self._max_tool_steps:
                raise ToolStepLimitError(
                    f"Stopped after {self._max_tool_steps} tool steps without a final answer."
                )
            steps += 1
            results = [self._run_tool(call) for call in calls]
            interaction = self._create(results, interaction.id)

        self._previous_id = interaction.id
        return interaction.output_text or ""

    def _create(self, input: Any, previous_id: str | None) -> Any:
        # Omit previous_interaction_id entirely on the first turn rather than sending None.
        kwargs = {"previous_interaction_id": previous_id} if previous_id else {}
        return self._client.interactions.create(
            model=self._model,
            input=input,
            tools=self._schemas,
            **kwargs,
        )

    @staticmethod
    def _function_calls(interaction: Any) -> list[Any]:
        return [s for s in (interaction.steps or []) if s.type == "function_call"]

    def _run_tool(self, call: Any) -> dict[str, Any]:
        arguments = dict(call.arguments or {})
        tool = self._tools.get(call.name)
        try:
            if tool is None:
                raise ValueError(f"Unknown tool: {call.name}")
            result, is_error = tool.func(**arguments), False
        except Exception as e:  # Errors go back to the model so it can recover.
            result, is_error = f"Error: {e}", True

        if self._on_tool_call:
            self._on_tool_call(call.name, arguments, result, is_error)

        return {
            "type": "function_result",
            "call_id": call.id,
            "name": call.name,
            "result": result,
            "is_error": is_error,
        }
