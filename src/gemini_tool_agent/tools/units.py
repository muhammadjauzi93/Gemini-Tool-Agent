"""Length, weight, and temperature conversion."""

from gemini_tool_agent.tools.base import Tool

# Each unit maps to (category, factor to convert it into the category's base unit).
UNITS = {
    "km": ("length", 1000), "m": ("length", 1), "cm": ("length", 0.01),
    "mi": ("length", 1609.344), "ft": ("length", 0.3048), "in": ("length", 0.0254),
    "kg": ("weight", 1), "g": ("weight", 0.001),
    "lb": ("weight", 0.45359237), "oz": ("weight", 0.028349523125),
    "c": ("temperature", None), "f": ("temperature", None), "k": ("temperature", None),
}  # fmt: skip


def convert_units(value: float, from_unit: str, to_unit: str) -> str:
    """Convert a value between length, weight, or temperature units."""
    from_unit, to_unit = from_unit.lower(), to_unit.lower()
    if from_unit not in UNITS or to_unit not in UNITS:
        raise ValueError(f"Unknown unit. Supported: {', '.join(UNITS)}")
    from_category, from_factor = UNITS[from_unit]
    to_category, to_factor = UNITS[to_unit]
    if from_category != to_category:
        raise ValueError(f"Can't convert {from_category} to {to_category}")

    if from_category == "temperature":
        # Convert to Celsius first, then to the target unit.
        celsius = {"c": value, "f": (value - 32) * 5 / 9, "k": value - 273.15}[from_unit]
        result = {"c": celsius, "f": celsius * 9 / 5 + 32, "k": celsius + 273.15}[to_unit]
    else:
        result = value * from_factor / to_factor

    return f"{value} {from_unit} = {round(result, 4)} {to_unit}"


CONVERT_UNITS = Tool(
    name="convert_units",
    description="Convert a value between units of length, weight, or temperature.",
    parameters={
        "type": "object",
        "properties": {
            "value": {"type": "number", "description": "The value to convert"},
            "from_unit": {"type": "string", "enum": list(UNITS)},
            "to_unit": {"type": "string", "enum": list(UNITS)},
        },
        "required": ["value", "from_unit", "to_unit"],
    },
    func=convert_units,
)
