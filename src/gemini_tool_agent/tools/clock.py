"""Current date and time lookup."""

from datetime import datetime
from zoneinfo import ZoneInfo

from gemini_tool_agent.tools.base import Tool


def get_current_datetime(timezone: str = "UTC") -> str:
    """Return the current date and time in an IANA timezone like 'Asia/Tokyo'."""
    now = datetime.now(ZoneInfo(timezone))
    return now.strftime("%A, %d %B %Y, %H:%M:%S %Z")


GET_CURRENT_DATETIME = Tool(
    name="get_current_datetime",
    description="Get the current date, day of the week, and time. Use this whenever the "
    "user asks about today, now, or anything relative to the current date.",
    parameters={
        "type": "object",
        "properties": {
            "timezone": {
                "type": "string",
                "description": "IANA timezone name, e.g. 'Asia/Kuala_Lumpur', "
                "'America/New_York'. Defaults to 'UTC'.",
            }
        },
    },
    func=get_current_datetime,
)
