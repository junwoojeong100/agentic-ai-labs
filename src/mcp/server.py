"""
MCP Server for Azure AI Foundry Agent Service

Provides tools via Model Context Protocol (MCP) using FastMCP with Streamable HTTP transport.
Runs with Streamable HTTP transport at http://0.0.0.0:8000/mcp by default.

Run locally:
  python server.py

Run in Azure Container Apps:
  Deployed automatically via Docker (see Dockerfile)

Tools provided:
  - get_weather(location): Get weather information for a city
  - calculate(expression): Perform mathematical calculations
  - get_current_time(): Get current date and time
  - generate_random_number(min, max): Generate random integer
"""
from __future__ import annotations

import os
import random
from datetime import datetime
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

# Server configuration
HOST = os.environ.get("MCP_HOST", "0.0.0.0")
PORT = int(os.environ.get("MCP_PORT", "8000"))
MOUNT_PATH = os.environ.get("MCP_MOUNT_PATH", "/mcp")

# Create FastMCP server
mcp = FastMCP(
    name="Azure Foundry MCP Server",
    instructions=(
        "This MCP server exposes tools for Azure AI Foundry Agent Service: "
        "get_weather(location), calculate(expression), get_current_time(), "
        "and generate_random_number(min, max)."
    ),
)

# =============================================================================
# MCP Tools - Exposed via Model Context Protocol
# =============================================================================
# These tools are callable by Azure AI Agents through the MCP protocol

@mcp.tool()
async def get_weather(location: str) -> Dict[str, Any]:
    """
    Get current weather information for a city.
    
    Args:
        location: City name (e.g., "Seoul", "Tokyo", "San Francisco")
    
    Returns:
        Dict containing temperature, condition, humidity, and timestamp
    """
    # Mock weather data (In production, use real weather API)
    temp = random.randint(15, 30)
    conditions = ["Sunny", "Cloudy", "Rainy", "Partly Cloudy"]
    condition = random.choice(conditions)
    humidity = random.randint(40, 80)
    
    weather_data = {
        "location": location,
        "temperature": f"{temp}°C",
        "condition": condition,
        "humidity": f"{humidity}%"
    }
    
    return weather_data


@mcp.tool()
async def calculate(expression: str) -> Dict[str, Any]:
    """
    Perform mathematical calculations.
    
    Args:
        expression: Mathematical expression (e.g., "2 + 2", "(10 * 5) / 2")
                   Supports: +, -, *, /, parentheses
    
    Returns:
        Dict containing the expression and calculated result, or error message
    """
    # Validate expression contains only allowed characters
    allowed_chars = set("0123456789+-*/() .")
    if not all(c in allowed_chars for c in expression):
        return {"error": "Invalid characters in expression"}
    
    try:
        # Use eval with restricted namespace for safety
        # Alternative: use ast.literal_eval or a proper math parser
        result = eval(expression, {"__builtins__": {}}, {})
        return {
            "expression": expression,
            "result": float(result)  # Ensure consistent number type
        }
    except Exception as e:
        return {"error": f"Calculation error: {str(e)}"}


@mcp.tool()
async def get_current_time() -> Dict[str, Any]:
    """
    Get current date and time in ISO format.
    
    Returns:
        Dict containing current_time (ISO format) and timezone
    """
    import time
    
    now = datetime.now()
    current_time = now.isoformat()
    timezone = time.tzname[0]
    
    result = {
        "current_time": current_time,
        "timezone": timezone,
        "timestamp": int(now.timestamp())
    }
    
    return result


@mcp.tool()
async def generate_random_number(min: int, max: int) -> Dict[str, Any]:
    """
    Generate a random integer between min and max (inclusive).
    
    Args:
        min: Minimum value (inclusive)
        max: Maximum value (inclusive)
    
    Returns:
        Dict containing the random_number, min, and max values
    """
    if min > max:
        return {"error": "min must be less than or equal to max"}
    
    random_num = random.randint(min, max)
    return {
        "random_number": random_num,
        "min": min,
        "max": max
    }


if __name__ == "__main__":
    # Configure FastMCP for streamable HTTP
    mcp.settings.host = HOST
    mcp.settings.port = PORT
    mcp.settings.streamable_http_path = MOUNT_PATH
    
    # Print startup info
    print("="*60)
    print("🚀 Starting Azure Foundry MCP Server (Streamable HTTP)")
    print("="*60)
    print(f"Server URL: http://{HOST}:{PORT}")
    print(f"MCP Endpoint: http://{HOST}:{PORT}{MOUNT_PATH}")
    print(f"\nMCP Protocol Endpoints:")
    print(f"  • POST {MOUNT_PATH} - MCP message handling (SSE)")
    print(f"\nTools available:")
    print(f"  • get_weather(location) - Get weather information")
    print(f"  • calculate(expression) - Perform calculations")
    print(f"  • get_current_time() - Get current time")
    print(f"  • generate_random_number(min, max) - Generate random number")
    print("="*60 + "\n")
    
    # Run FastMCP server with streamable-http transport
    # This automatically creates a FastAPI app with the MCP endpoints
    mcp.run(transport="streamable-http")
