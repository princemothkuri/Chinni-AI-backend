from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from datetime import datetime
from pytz import timezone

class CurrentDateTimeFetcher(BaseTool):
    """
    CurrentDateTimeFetcher is a tool that provides the current date and time for India.

    Purpose:
    - Useful for scenarios where accurate and localized date and time information is required for India.
    - Supports multiple formats for flexibility: ISO 8601 format or human-readable format.

    Functionality:
    - Fetches the current date and time in the Indian Standard Time (IST) timezone.
    - Accepts a format option as input to determine the output style.

    Usage:
    - Accepts `format_type` as input, which can be "ISO" for ISO 8601 format or "human" for a human-readable string.
    - Returns the current date and time as per the specified format.

    Example:
    - Input: `format_type="human"`
    - Output: `"28 November 2024, 02:45 PM"`
    """
    name: str = "CurrentDateTimeFetcher"
    description: str = (
        "Provides the current date and time for India in the specified format. "
        "Accepts `format_type` as input, either 'ISO' for ISO 8601 format or 'human' for human-readable format."
    )

    class InputSchema(BaseModel):
        format_type: str = Field(..., description="The desired output format: 'ISO' or 'human'.")

    def _run(self, format_type: str):
        """Fetches the current date and time in IST and returns it in the specified format."""
        try:
            india_timezone = timezone("Asia/Kolkata")
            current_time = datetime.now(india_timezone)

            if format_type.lower() == "iso":
                print("CurrentDateTimeFetcher >>> ISO: ", current_time.isoformat())
                return current_time.isoformat()
            elif format_type.lower() == "human":
                print("CurrentDateTimeFetcher >>> human: ", current_time.strftime("%d %B %Y, %I:%M %p"))
                return current_time.strftime("%d %B %Y, %I:%M %p")
            else:
                return "Invalid format_type. Use 'ISO' or 'human'."
        except Exception as e:
            return f"An error occurred while fetching the date and time: {str(e)}"
