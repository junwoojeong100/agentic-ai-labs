"""
MCP Server for Azure AI Foundry Agent Service - Weather Information Service

Provides accurate weather information via Model Context Protocol (MCP) using FastMCP 
with Streamable HTTP transport. Runs at http://0.0.0.0:8000/mcp by default.

Run locally:
  python server.py

Run in Azure Container Apps:
  Deployed automatically via Docker (see Dockerfile)

Weather Data Provider:
  - Primary: OpenWeatherMap API (https://openweathermap.org)
  - Fallback: wttr.in free service (https://wttr.in)
  
Tools provided:
  - get_weather(location): Get real-time weather information for any city worldwide
    * Supports Korean/English city names
    * Returns temperature, conditions, humidity, wind speed, feels-like temp
    * No API key required (uses wttr.in free service)
"""
from __future__ import annotations

import os
from typing import Any, Dict

import httpx
from mcp.server.fastmcp import FastMCP

# Server configuration
HOST = os.environ.get("MCP_HOST", "0.0.0.0")
PORT = int(os.environ.get("MCP_PORT", "8000"))
MOUNT_PATH = os.environ.get("MCP_MOUNT_PATH", "/mcp")

# Create FastMCP server
mcp = FastMCP(
    name="Azure Foundry Weather MCP Server",
    instructions=(
        "This MCP server provides accurate real-time weather information for any city worldwide. "
        "It supports Korean and English city names. Use get_weather(location) to get current weather conditions, "
        "temperature, humidity, wind speed, and more. The service uses wttr.in API which provides reliable "
        "weather data without requiring API keys."
    ),
)

# =============================================================================
# MCP Tools - Exposed via Model Context Protocol
# =============================================================================
# These tools are callable by Azure AI Agents through the MCP protocol

@mcp.tool()
async def get_weather(location: str) -> Dict[str, Any]:
    """
    Get accurate real-time weather information for any city worldwide.
    
    This tool uses wttr.in, a reliable weather service that provides:
    - Current temperature and feels-like temperature
    - Weather conditions (clear, cloudy, rainy, etc.)
    - Humidity percentage
    - Wind speed and direction
    - Observation time
    
    Args:
        location: City name in English or Korean (e.g., "Seoul", "서울", "Tokyo", "San Francisco")
    
    Returns:
        Dict containing:
        - location: Location name
        - temperature: Current temperature in Celsius
        - feels_like: Feels-like temperature in Celsius
        - condition: Weather condition description
        - humidity: Humidity percentage
        - wind_speed: Wind speed in km/h
        - observation_time: When the data was observed
        - data_source: API source used
    
    Example:
        >>> await get_weather("Seoul")
        {
            "location": "Seoul, South Korea",
            "temperature": "8°C",
            "feels_like": "5°C",
            "condition": "Partly cloudy",
            "humidity": "62%",
            "wind_speed": "15 km/h",
            "observation_time": "2025-10-06 14:30",
            "data_source": "wttr.in"
        }
    """
    try:
        # Use wttr.in API - free, reliable, no API key required
        # Format: https://wttr.in/{location}?format=j1
        url = f"https://wttr.in/{location}?format=j1"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
        
        # Extract current conditions
        current = data.get("current_condition", [{}])[0]
        nearest_area = data.get("nearest_area", [{}])[0]
        
        # Parse location name
        area_name = nearest_area.get("areaName", [{}])[0].get("value", location)
        country = nearest_area.get("country", [{}])[0].get("value", "")
        location_display = f"{area_name}, {country}" if country else area_name
        
        # Parse weather data
        temp_c = current.get("temp_C", "N/A")
        feels_like_c = current.get("FeelsLikeC", "N/A")
        condition_desc = current.get("weatherDesc", [{}])[0].get("value", "Unknown")
        humidity = current.get("humidity", "N/A")
        wind_speed = current.get("windspeedKmph", "N/A")
        wind_dir = current.get("winddir16Point", "")
        observation_time = current.get("observation_time", "N/A")
        
        weather_data = {
            "location": location_display,
            "temperature": f"{temp_c}°C",
            "feels_like": f"{feels_like_c}°C",
            "condition": condition_desc,
            "humidity": f"{humidity}%",
            "wind_speed": f"{wind_speed} km/h" + (f" {wind_dir}" if wind_dir else ""),
            "observation_time": observation_time,
            "data_source": "wttr.in (real-time weather data)"
        }
        
        return weather_data
        
    except httpx.HTTPError as e:
        return {
            "error": f"Failed to fetch weather data for '{location}'",
            "details": f"HTTP error: {str(e)}",
            "suggestion": "Please check the city name spelling or try a major city name in English."
        }
    except Exception as e:
        return {
            "error": f"Unexpected error getting weather for '{location}'",
            "details": str(e),
            "suggestion": "Please try again with a different city name."
        }


# =============================================================================
# Additional utility tools can be added here
# =============================================================================
# Keep the server focused on providing high-quality weather information.
# If you need more tools, consider creating separate specialized MCP servers.


if __name__ == "__main__":
    # Configure FastMCP for streamable HTTP
    mcp.settings.host = HOST
    mcp.settings.port = PORT
    mcp.settings.streamable_http_path = MOUNT_PATH
    
    # Print startup info
    print("="*70)
    print("🌤️  Starting Azure Foundry Weather MCP Server (Streamable HTTP)")
    print("="*70)
    print(f"Server URL: http://{HOST}:{PORT}")
    print(f"MCP Endpoint: http://{HOST}:{PORT}{MOUNT_PATH}")
    print(f"\nMCP Protocol Endpoints:")
    print(f"  • POST {MOUNT_PATH} - MCP message handling (SSE)")
    print(f"\nWeather Service:")
    print(f"  • Data Provider: wttr.in (real-time weather API)")
    print(f"  • Coverage: Worldwide cities")
    print(f"  • Languages: Korean, English, and more")
    print(f"\nAvailable Tool:")
    print(f"  • get_weather(location) - Get accurate real-time weather information")
    print(f"    - Example: get_weather('Seoul') or get_weather('서울')")
    print(f"    - Returns: temperature, feels-like, condition, humidity, wind")
    print("="*70 + "\n")
    
    # Run FastMCP server with streamable-http transport
    # This automatically creates a FastAPI app with the MCP endpoints
    mcp.run(transport="streamable-http")
