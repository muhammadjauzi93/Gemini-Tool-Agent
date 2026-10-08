# Gemini Tool Agent

![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-Interactions_API-8E75B2?logo=googlegemini&logoColor=white)
![SDK](https://img.shields.io/badge/SDK-google--genai-4285F4?logo=google&logoColor=white)
![Tests](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)
![Lint](https://img.shields.io/badge/lint-ruff-D7FF64?logo=ruff&logoColor=black)

A terminal chat agent built on the Google Gemini Interactions API that answers questions by calling local Python tools. It implements the core agentic pattern: a multi-turn chat loop with server-side conversation memory, wrapped around a bounded tool-calling loop.

---

## Features

- **Agentic tool loop**: Executes model-requested function calls, returns results, and repeats until the model produces a final answer. Bounded by `MAX_TOOL_STEPS`.
- **Server-side conversation memory**: Chains turns with `previous_interaction_id`, so full history is retained without resending it. `/reset` starts a fresh conversation.
- **Six built-in tools**: Arithmetic, current date/time, unit conversion, random numbers, dice rolls, and exact text counting.
- **Sandboxed calculator**: Parses expressions with `ast` against an operator allow list instead of using `eval()`, and caps exponents at 1000.
- **Error feedback to the model**: Tool exceptions and unknown tool names are returned as `function_result` steps with `is_error: true`, so the model can recover.
- **Pluggable tool registry**: Each tool is a self-contained `Tool` (function plus JSON Schema). Adding one requires no changes to the agent.
- **Environment-driven configuration**: Model, step limit, and trace output are set via `.env`, validated at startup with clear errors.
- **Testable core**: The `Agent` class takes an injected client, so the full tool loop is unit-tested without network calls.

---

## Architecture

```text
.
├── .github/workflows/ci.yml       # Lint, format check, and tests on Python 3.10 and 3.12
├── src/gemini_tool_agent/
│   ├── __init__.py                # Public API: Agent, ToolStepLimitError
│   ├── __main__.py                # Enables `python -m gemini_tool_agent`
│   ├── cli.py                     # Interactive terminal interface (REPL)
│   ├── agent.py                   # Agent: conversation memory + tool-calling loop
│   ├── config.py                  # Settings loaded and validated from the environment
│   └── tools/
│       ├── __init__.py            # Tool registry (ALL_TOOLS)
│       ├── base.py                # Tool dataclass and schema serialisation
│       ├── calculator.py          # calculate
│       ├── clock.py               # get_current_datetime
│       ├── units.py               # convert_units
│       ├── randomness.py          # random_number, roll_dice
│       └── text.py                # count_text
├── tests/
│   ├── test_agent.py              # Tool loop, history chaining, errors, step limit
│   └── test_tools.py              # Tool behaviour, safety, and schema validity
├── .env.example                   # Environment variable template
├── pyproject.toml                 # Package metadata, dependencies, tool config
└── requirements.txt               # Shortcut: editable install with all extras
```

| Layer | Module | Responsibility |
|---|---|---|
| Interface | `cli.py` | Reads input, handles commands and errors, prints replies and tool traces |
| Orchestration | `agent.py` | Calls the API, runs requested tools, chains interactions, enforces the step limit |
| Configuration | `config.py` | Loads `.env`, validates values, exposes an immutable `Settings` |
| Capabilities | `tools/` | Pure Python tool functions plus their JSON Schema declarations |

### Request flow

```text
cli.main ──► Agent.send(message)
               │
               ▼
          interactions.create(input, tools, previous_interaction_id)
               │
               ├── function_call steps present?
               │      ├── yes → Tool.func(**arguments) → function_result
               │      │         → interactions.create(input=[results...],
               │      │                               previous_interaction_id=<current id>)
               │      │         → repeat (raises ToolStepLimitError past MAX_TOOL_STEPS)
               │      └── no  → return output_text
               ▼
          previous_id = interaction.id    # carried into the next turn
```

---

## Getting Started

### Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10+ | Developed on 3.12. CI tests 3.10 and 3.12 |
| Gemini API key | — | Create one at [Google AI Studio](https://aistudio.google.com/apikey) |

### Installation

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` installs the package in editable mode with the `dev` and `experiments` extras. To choose extras explicitly:

| Command | Installs |
|---|---|
| `pip install -e .` | Runtime only: `google-genai`, `python-dotenv`, `tzdata` (Windows) |
| `pip install -e ".[dev]"` | Runtime + `pytest`, `ruff` |
| `pip install -e ".[dev,experiments]"` | Runtime + dev + `anthropic`, `openai`, `httpx`, `requests`, `pydantic`, `tiktoken`, `rich` |

> If PowerShell blocks `Activate.ps1`, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

### Environment Configuration

Copy the template and set your API key:

```powershell
Copy-Item .env.example .env
```

```bash
cp .env.example .env
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | Yes¹ | — | Gemini API key used by `genai.Client()` |
| `GOOGLE_API_KEY` | No¹ | — | Alternative key variable. Takes priority in the SDK if both are set |
| `GEMINI_MODEL` | No | `gemini-3.8-flash` | Model ID used for every request |
| `MAX_TOOL_STEPS` | No | `10` | Maximum tool-call rounds per user message (positive integer) |
| `SHOW_TOOL_CALLS` | No | `true` | Print `[tool]` trace lines (`true`/`false`) |
| `ANTHROPIC_API_KEY` | No | — | Not used by the agent; for experiments with the `anthropic` SDK |
| `OPENAI_API_KEY` | No | — | Not used by the agent; for experiments with the `openai` SDK |

¹ One of `GEMINI_API_KEY` or `GOOGLE_API_KEY` must be set; otherwise the CLI exits with a configuration error.

Variables already set in the shell take precedence over `.env`.

---

## Usage

### Start the agent

```bash
gemini-agent
```

Equivalent without the console script:

```bash
python -m gemini_tool_agent
```

### Single tool call

```text
You: What is 1234 * 5678?
  [tool] calculate({'expression': '1234 * 5678'})
  [tool] -> 7006652
AI: 1234 × 5678 = 7,006,652.
```

### Chained tool calls

```text
You: What's 100°C in Fahrenheit, and what time is it in Kuala Lumpur?
  [tool] convert_units({'value': 100, 'from_unit': 'c', 'to_unit': 'f'})
  [tool] -> 100 c = 212.0 f
  [tool] get_current_datetime({'timezone': 'Asia/Kuala_Lumpur'})
  [tool] -> Friday, 09 October 2026, 14:05:12 +08
AI: 100°C is 212°F. In Kuala Lumpur it's currently 2:05 PM on Friday, 9 October 2026.
```

### Error recovery

```text
You: Convert 5 kg to feet.
  [tool] convert_units({'value': 5, 'from_unit': 'kg', 'to_unit': 'ft'})
  [tool] -> Error: Can't convert weight to length
AI: Kilograms measure weight and feet measure length, so they can't be converted.
```

### Multi-turn memory

```text
You: My name is Sam.
AI: Nice to meet you, Sam!

You: How many letters are in my name?
  [tool] count_text({'text': 'Sam'})
  [tool] -> {"words": 1, "characters": 3, "characters_without_spaces": 3}
AI: Your name, Sam, has 3 letters.
```

> Model responses are illustrative. Wording varies between runs.

### Using the agent as a library

```python
from google import genai

from gemini_tool_agent import Agent
from gemini_tool_agent.tools import ALL_TOOLS

agent = Agent(client=genai.Client(), tools=ALL_TOOLS, model="gemini-3.8-flash")
print(agent.send("Roll two dice and add 10 to the total."))
```

### Adding a tool

1. **Create** `src/gemini_tool_agent/tools/strings.py` with the function and its `Tool` declaration:

   ```python
   from gemini_tool_agent.tools.base import Tool


   def reverse_text(text: str) -> str:
       """Reverse a string."""
       return text[::-1]


   REVERSE_TEXT = Tool(
       name="reverse_text",
       description="Reverse the characters of a string.",
       parameters={
           "type": "object",
           "properties": {"text": {"type": "string"}},
           "required": ["text"],
       },
       func=reverse_text,
   )
   ```

2. **Register** it in `src/gemini_tool_agent/tools/__init__.py`:

   ```python
   from gemini_tool_agent.tools.strings import REVERSE_TEXT

   ALL_TOOLS: list[Tool] = [
       # ...
       REVERSE_TEXT,
   ]
   ```

3. **Test** it in `tests/test_tools.py`. The registry test automatically checks name uniqueness and schema shape.

---

## Reference

### Tools

| Tool | Parameters | Returns | Constraints |
|---|---|---|---|
| `calculate` | `expression: str` *(required)* | Result as a string | Operators `+ - * / ** %`, unary `-`, parentheses. Exponent ≤ 1000. Names and calls are rejected |
| `get_current_datetime` | `timezone: str = "UTC"` | e.g. `Friday, 09 October 2026, 14:05:12 +08` | IANA zone names only (e.g. `America/New_York`) |
| `convert_units` | `value: number`, `from_unit: str`, `to_unit: str` *(all required)* | e.g. `10 km = 6.2137 mi` | Same category only. Rounded to 4 decimal places |
| `random_number` | `min: int`, `max: int` *(required)* | Integer as a string | Inclusive range |
| `roll_dice` | `sides: int = 6`, `count: int = 1` | JSON `{"rolls": [...], "total": n}` | `sides` 2–1000, `count` 1–100 |
| `count_text` | `text: str` *(required)*, `letter: str = ""` | JSON with `words`, `characters`, `characters_without_spaces`, and optional `occurrences_of_'<letter>'` | Letter matching is case-insensitive. Words are split on whitespace |

### Supported units

| Category | Units |
|---|---|
| Length | `km`, `m`, `cm`, `mi`, `ft`, `in` |
| Weight | `kg`, `g`, `lb`, `oz` |
| Temperature | `c`, `f`, `k` |

### CLI commands

| Input | Effect |
|---|---|
| `exit`, `quit` | End the session (case-insensitive). `Ctrl+C` and `Ctrl+D` also exit cleanly |
| `/reset` | Discard conversation history and start a new conversation |
| Empty line | Ignored; no API call is made |

### `Agent` API

| Member | Description |
|---|---|
| `Agent(client, tools, model, max_tool_steps=10, on_tool_call=None)` | `on_tool_call(name, arguments, result, is_error)` is invoked after each tool runs |
| `send(message) -> str` | Sends a message, runs any requested tools, returns the final text. Raises `ToolStepLimitError` past the step limit |
| `reset()` | Starts a new conversation |

### Exit codes

| Code | Meaning |
|---|---|
| `0` | Normal exit |
| `1` | Configuration error (missing API key or invalid setting) |

---

## Development

| Task | Command |
|---|---|
| Run tests | `pytest` |
| Lint | `ruff check .` |
| Auto-fix lint issues | `ruff check . --fix` |
| Format | `ruff format .` |
| Check formatting (CI) | `ruff format --check .` |

Tests make no network calls: `tests/test_agent.py` drives the agent with an in-memory fake client.

---

## Limitations

- **History lives on the server, not on disk.** Restarting the CLI starts a new conversation.
- **Latency scales with tool use.** Each tool round adds one API request, and long conversations increase input size on every turn.
- **Responses are not streamed.** Output appears only after the model has finished generating.

---

## Contributing

1. Create a feature branch:

   ```bash
   git checkout -b feature/<short-description>
   ```

2. Keep each tool self-contained in its own module under `src/gemini_tool_agent/tools/`.
3. Add or update tests, then confirm all checks pass:

   ```bash
   ruff check . && ruff format --check . && pytest
   ```

4. Never commit `.env`. Confirm it is excluded with:

   ```bash
   git check-ignore .env
   ```

5. Commit with a descriptive message and open a pull request against `main`.

---

## License

No license has been selected yet. Until a `LICENSE` file is added, all rights are reserved by the author.
