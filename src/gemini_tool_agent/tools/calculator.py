"""Safe arithmetic evaluation without eval()."""

import ast
import operator

from gemini_tool_agent.tools.base import Tool

MAX_EXPONENT = 1000

# Only these operators are allowed, so the model can't run arbitrary code.
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


def calculate(expression: str) -> str:
    """Safely evaluate a math expression like '(12 + 3) * 4 / 2'."""

    def evaluate(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            left, right = evaluate(node.left), evaluate(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > MAX_EXPONENT:
                raise ValueError(f"Exponent too large (max {MAX_EXPONENT})")
            return OPERATORS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
            return OPERATORS[type(node.op)](evaluate(node.operand))
        raise ValueError(f"Unsupported expression: {expression}")

    return str(evaluate(ast.parse(expression, mode="eval").body))


CALCULATE = Tool(
    name="calculate",
    description="Evaluate an arithmetic expression. Use this for any math instead of "
    "calculating in your head. Supports + - * / ** % and parentheses.",
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The expression to evaluate, e.g. '(12 + 3) * 4'",
            }
        },
        "required": ["expression"],
    },
    func=calculate,
)
