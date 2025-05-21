from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP 


# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "MCP-Python-Weather-App/1.0"

# Helper functions
async def make_nws_request(url: str) -> dict[str, Any] | None:
    """
    Make a request to the NWS API and return the JSON response.
    """
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            print(f"Request error: {e}")
            return None

def format_alert(feature: dict) -> str:
    """
    Format an alert feature into a readable string.
    """
    props = feature["properties"]
    
    ret_string = f"""
    Event: {props.get('event','Unknown')}
    Area: {props.get('areaDesc','Unknown')}
    Severity: {props.get('severity','Unknown')}
    Description: {props.get('description','Unknown')}
    Instruction: {props.get('instruction','Unknown')}"""
    
    return ret_string


@mcp.tool()
async def get_alerts(state: str) -> str:
    """
    Get weather alerts for a specific state.
    
    Args:
        state (str): The state abbreviation (e.g., "CA" for California).
    """
    url = f"{NWS_API_BASE}/alerts/active/area={state}"
    data = await make_nws_request(url)
    
    if data is None :
        return "Failed to fetch alerts."
    
    features = data.get("features", [])
    
    if not features:
        return "No active alerts."
    
    alerts = [format_alert(feature) for feature in features]
    
    return "\n".join(alerts)

@mcp.tool()
async def get_forecast(lat: float, lon: float) -> str:
    """Get weather forecast for a location.

    Args:
        lat (float): latitude of the location
        lon (float): longitude of the location

    Returns:
        str: _description_
    """
    
    # First get the forecast grid endpoint
    point_url = f"{NWS_API_BASE}/points/{lat},{lon}"
    point_data = await make_nws_request(point_url)
    
    if point_data is None:
        return "Failed to fetch forecast grid."
    
    forecast_url = point_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)
    
    if forecast_data is None:
        return "Failed to fetch forecast data."
    
    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]: # Only show the next 5 periods
        forecast = f"""
        {period['name']}:
        Temperature: {period['temperature']}°{period['temperatureUnit']}
        Wind: {period['windSpeed']} {period['windDirection']}
        Forecast: {period['detailedForecast']}
        """
        forecasts.append(forecast)
    return "\n".join(forecasts)

@mcp.tool()
def get_location(lat: float, lon: float) -> str:
    """Getting location given latitude and longitude.

    Args:
        lat (float): _latitude of the location
        lon (float): _longitude of the location

    Returns:
        str: _location name
    """
    
    # First get the forecast grid endpoint
    point_url = f"{NWS_API_BASE}/points/{lat},{lon}"
    point_data = FastMCP.make_request(point_url)
    
    if point_data is None:
        return "Failed to fetch forecast grid."
    
    location = point_data["properties"]["relativeLocation"]["properties"]["city"]
    
    return location

# Run the server
if __name__ == "__main__":
    mcp.run()
    
'''
What happens when this server is connected to Claude Desktop:

What’s happening under the hood
When you ask a question (e.g., "What’s the weather like in San Francisco?"), the following steps occur:

- The client sends your question to Claude
- Claude analyzes the available tools and decides which one(s) to use
- The client executes the chosen tool(s) through the MCP server
- The results are sent back to Claude
- Claude formulates a natural language response
- The response is displayed to you!
'''