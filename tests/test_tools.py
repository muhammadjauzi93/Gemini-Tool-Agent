import json
from zoneinfo import ZoneInfoNotFoundError

import pytest

from gemini_tool_agent.tools import ALL_TOOLS
from gemini_tool_agent.tools.calculator import calculate
from gemini_tool_agent.tools.clock import get_current_datetime
from gemini_tool_agent.tools.randomness import random_number, roll_dice
from gemini_tool_agent.tools.text import count_text
from gemini_tool_agent.tools.units import convert_units


@pytest.mark.parametrize(
    ("expression", "expected"),
    [("(12 + 3) * 4 / 2", "30.0"), ("2 ** 10", "1024"), ("-5 % 3", "1"), ("2 * -3", "-6")],
)
def test_calculate(expression, expected):
    assert calculate(expression) == expected


@pytest.mark.parametrize(
    "expression", ['__import__("os")', "open('.env').read()", "x + 1", "9 ** 9 ** 9", "7 // 2"]
)
def test_calculate_rejects_unsafe_or_unsupported(expression):
    with pytest.raises(ValueError):
        calculate(expression)


def test_calculate_division_by_zero():
    with pytest.raises(ZeroDivisionError):
        calculate("1 / 0")


def test_get_current_datetime_with_timezone():
    assert get_current_datetime("Asia/Kuala_Lumpur").endswith("+08")


def test_get_current_datetime_unknown_timezone():
    with pytest.raises(ZoneInfoNotFoundError):
        get_current_datetime("Mars/Base")


@pytest.mark.parametrize(
    ("value", "from_unit", "to_unit", "expected"),
    [
        (10, "km", "mi", "10 km = 6.2137 mi"),
        (100, "C", "F", "100 c = 212.0 f"),
        (0, "k", "c", "0 k = -273.15 c"),
        (1, "lb", "g", "1 lb = 453.5924 g"),
    ],
)
def test_convert_units(value, from_unit, to_unit, expected):
    assert convert_units(value, from_unit, to_unit) == expected


@pytest.mark.parametrize(("from_unit", "to_unit"), [("kg", "ft"), ("km", "parsec")])
def test_convert_units_invalid(from_unit, to_unit):
    with pytest.raises(ValueError):
        convert_units(1, from_unit, to_unit)


def test_random_number_in_range():
    assert all(1 <= int(random_number(1, 3)) <= 3 for _ in range(50))


def test_roll_dice():
    result = json.loads(roll_dice(sides=20, count=3))
    assert len(result["rolls"]) == 3
    assert all(1 <= r <= 20 for r in result["rolls"])
    assert result["total"] == sum(result["rolls"])


@pytest.mark.parametrize(("sides", "count"), [(1, 1), (6, 0), (6, 101)])
def test_roll_dice_limits(sides, count):
    with pytest.raises(ValueError):
        roll_dice(sides, count)


def test_count_text():
    result = json.loads(count_text("Strawberry jam", letter="r"))
    assert result == {
        "words": 2,
        "characters": 14,
        "characters_without_spaces": 13,
        "occurrences_of_'r'": 3,
    }


def test_registry_names_are_unique_and_schemas_valid():
    names = [tool.name for tool in ALL_TOOLS]
    assert len(names) == len(set(names))
    for tool in ALL_TOOLS:
        schema = tool.schema()
        assert schema["type"] == "function"
        assert schema["parameters"]["type"] == "object"
