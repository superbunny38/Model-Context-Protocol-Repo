from fastmcp import FastMCP
import datetime
import pytz
import os

# client: ex.) Claude

mcp = FastMCP(
    name = "Current Date and Time",
    instructions = "When you are asked for current date or time, call current_datetime() and pass along an optional timezone parameter (defaults to NYC)."
)

@mcp.tool()
def current_datetime(timezone: str = "America/New_York") -> str:
    """
    Returns the current date and time as a string.
    If you are asked for the current date or time, call this function.
    Args:
        timezone: Timezone name (e.g., 'UTC', 'US/Pacific', 'Europe/London').
        Defaults to 'America/New_York'
    """
    
    
    try:
        tz = pytz.timezone(timezone)
        now = datetime.datetime.now(tz)
        return now.strftime("%Y-%m0%d %H:%M:%S %Z")
    except pytz.exceptions.UnknownTimeZoneError:
        return f"Error: Unknown timezone '{timezone}'. Please use a valid timezone name."
    
if __name__ == "__main__":
    mcp.run()