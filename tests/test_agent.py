from types import SimpleNamespace

import pytest

from gemini_tool_agent.agent import Agent, ToolStepLimitError
from gemini_tool_agent.tools import ALL_TOOLS


def text_reply(id, text):
    return SimpleNamespace(id=id, steps=[], output_text=text)


def tool_reply(id, name, arguments, call_id="call-1"):
    call = SimpleNamespace(type="function_call", id=call_id, name=name, arguments=arguments)
    return SimpleNamespace(id=id, steps=[call], output_text=None)


class FakeClient:
    """Returns queued interactions and records every create() call."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []
        self.interactions = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.replies.pop(0)


def make_agent(client, **kwargs):
    return Agent(client=client, tools=ALL_TOOLS, model="test-model", **kwargs)


def test_plain_reply_without_tools():
    client = FakeClient(text_reply("i1", "Hello!"))
    assert make_agent(client).send("Hi") == "Hello!"
    assert "previous_interaction_id" not in client.calls[0]
    assert len(client.calls[0]["tools"]) == len(ALL_TOOLS)


def test_conversation_history_is_chained():
    client = FakeClient(text_reply("i1", "Nice to meet you"), text_reply("i2", "Sam"))
    agent = make_agent(client)
    agent.send("My name is Sam")
    agent.send("What's my name?")
    assert client.calls[1]["previous_interaction_id"] == "i1"


def test_reset_starts_new_conversation():
    client = FakeClient(text_reply("i1", "a"), text_reply("i2", "b"))
    agent = make_agent(client)
    agent.send("first")
    agent.reset()
    agent.send("second")
    assert "previous_interaction_id" not in client.calls[1]


def test_tool_call_result_is_sent_back():
    client = FakeClient(
        tool_reply("i1", "calculate", {"expression": "6 * 7"}),
        text_reply("i2", "The answer is 42."),
    )
    seen = []
    agent = make_agent(client, on_tool_call=lambda *args: seen.append(args))

    assert agent.send("What is 6 * 7?") == "The answer is 42."
    followup = client.calls[1]
    assert followup["previous_interaction_id"] == "i1"
    assert followup["input"] == [
        {
            "type": "function_result",
            "call_id": "call-1",
            "name": "calculate",
            "result": "42",
            "is_error": False,
        }
    ]
    assert seen == [("calculate", {"expression": "6 * 7"}, "42", False)]


@pytest.mark.parametrize(
    ("name", "arguments"),
    [("convert_units", {"value": 1, "from_unit": "kg", "to_unit": "ft"}), ("no_such_tool", {})],
)
def test_tool_errors_are_returned_to_model(name, arguments):
    client = FakeClient(tool_reply("i1", name, arguments), text_reply("i2", "Sorry."))
    make_agent(client).send("do it")
    result = client.calls[1]["input"][0]
    assert result["is_error"] is True
    assert result["result"].startswith("Error:")


def test_step_limit_stops_runaway_loop():
    client = FakeClient(*[tool_reply(f"i{n}", "roll_dice", {}) for n in range(5)])
    agent = make_agent(client, max_tool_steps=2)
    with pytest.raises(ToolStepLimitError):
        agent.send("roll forever")
    assert len(client.calls) == 3  # initial request + 2 tool rounds


def test_final_answer_on_last_allowed_step_is_returned():
    client = FakeClient(tool_reply("i1", "roll_dice", {}), text_reply("i2", "Done"))
    assert make_agent(client, max_tool_steps=1).send("roll once") == "Done"
