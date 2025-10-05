"""
MCP Client for testing the MCP server tools.

This client connects to the MCP server and allows testing of the available tools:
- calculate: Perform mathematical calculations
- get_weather: Get weather information for a city
- get_current_time: Get current date and time
- generate_random_number: Generate a random number in a range
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
import httpx


def parse_sse_response(response_text: str) -> Optional[Dict[str, Any]]:
    """Parse Server-Sent Events (SSE) response from FastMCP."""
    lines = response_text.strip().split('\n')
    for line in lines:
        if line.startswith('data: '):
            json_str = line[6:]  # Remove 'data: ' prefix
            return json.loads(json_str)
    return None


class MCPClient:
    """Client for interacting with MCP server using the MCP protocol."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize MCP client.
        
        Args:
            base_url: Base URL of the MCP server
        """
        self.base_url = base_url
        self.mcp_endpoint = f"{base_url}/mcp"
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.session_id: Optional[str] = None
        self.request_id = 0
    
    async def _get_next_id(self) -> int:
        """Get next request ID."""
        self.request_id += 1
        return self.request_id
    
    async def initialize(self) -> Optional[str]:
        """
        Initialize MCP session.
        
        Returns:
            Session ID if successful
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        
        init_payload = {
            "jsonrpc": "2.0",
            "id": await self._get_next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "mcp-test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        response = await self.http_client.post(
            self.mcp_endpoint,
            json=init_payload,
            headers=headers
        )
        response.raise_for_status()
        
        # Extract session ID from headers
        self.session_id = response.headers.get('mcp-session-id')
        
        # Send initialized notification
        if self.session_id:
            headers['mcp-session-id'] = self.session_id
            initialized_payload = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            await self.http_client.post(
                self.mcp_endpoint,
                json=initialized_payload,
                headers=headers
            )
        
        return self.session_id
    
    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools from the MCP server.
        
        Returns:
            List of available tools with their descriptions
        """
        if not self.session_id:
            await self.initialize()
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": self.session_id
        }
        
        list_payload = {
            "jsonrpc": "2.0",
            "id": await self._get_next_id(),
            "method": "tools/list",
            "params": {}
        }
        
        response = await self.http_client.post(
            self.mcp_endpoint,
            json=list_payload,
            headers=headers
        )
        response.raise_for_status()
        
        result = parse_sse_response(response.text)
        if result and 'result' in result:
            return result['result'].get('tools', [])
        return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a specific tool on the MCP server using MCP protocol.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            Result from the tool execution
        """
        if not self.session_id:
            await self.initialize()
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": self.session_id
        }
        
        call_payload = {
            "jsonrpc": "2.0",
            "id": await self._get_next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        try:
            response = await self.http_client.post(
                self.mcp_endpoint,
                json=call_payload,
                headers=headers
            )
            response.raise_for_status()
            
            result = parse_sse_response(response.text)
            
            if result and "error" in result:
                print(f"Tool error: {result['error']}")
                return None
            
            # Extract result from MCP response
            if result and "result" in result:
                return result["result"]
            
            return result
        except Exception as e:
            print(f"Error calling tool '{tool_name}': {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def calculate(self, expression: str) -> Optional[float]:
        """
        Perform a mathematical calculation.
        
        Args:
            expression: Mathematical expression to evaluate (e.g., "2 + 2")
            
        Returns:
            Result of the calculation
        """
        result = await self.call_tool("calculate", {"expression": expression})
        if result and isinstance(result, dict):
            # Handle MCP content response format
            if "structuredContent" in result:
                return result["structuredContent"]["result"].get("result")
            elif "content" in result:
                for item in result["content"]:
                    if item.get("type") == "text":
                        try:
                            data = json.loads(item["text"])
                            return data.get("result")
                        except:
                            return float(item["text"])
        return None
    
    async def get_weather(self, city: str) -> Optional[Dict[str, Any]]:
        """
        Get weather information for a city.
        
        Args:
            city: Name of the city
            
        Returns:
            Weather information dictionary
        """
        result = await self.call_tool("get_weather", {"location": city})
        if result and isinstance(result, dict):
            # Handle MCP content response format
            if "structuredContent" in result:
                return result["structuredContent"]["result"]
            elif "content" in result:
                for item in result["content"]:
                    if item.get("type") == "text":
                        return json.loads(item["text"])
        return None
    
    async def get_current_time(self) -> Optional[Dict[str, Any]]:
        """
        Get current date and time.
        
        Returns:
            Current time information dictionary
        """
        result = await self.call_tool("get_current_time", {})
        if result and isinstance(result, dict):
            # Handle MCP content response format
            if "structuredContent" in result:
                return result["structuredContent"]["result"]
            elif "content" in result:
                for item in result["content"]:
                    if item.get("type") == "text":
                        return json.loads(item["text"])
        return None
    
    async def generate_random_number(
        self, 
        min_value: int = 1, 
        max_value: int = 100
    ) -> Optional[int]:
        """
        Generate a random number in a range.
        
        Args:
            min_value: Minimum value (inclusive)
            max_value: Maximum value (inclusive)
            
        Returns:
            Random number
        """
        result = await self.call_tool(
            "generate_random_number",
            {"min": min_value, "max": max_value}
        )
        if result and isinstance(result, dict):
            # Handle MCP content response format
            if "structuredContent" in result:
                return result["structuredContent"]["result"].get("random_number")
            elif "content" in result:
                for item in result["content"]:
                    if item.get("type") == "text":
                        data = json.loads(item["text"])
                        return data.get("random_number")
        return None


async def test_client():
    """Test the MCP client with all available tools."""
    client = MCPClient()
    
    try:
        print("=" * 60)
        print("MCP Client Test Suite")
        print("=" * 60)
        
        # Initialize session
        print("\n[Init] Initializing MCP session...")
        session_id = await client.initialize()
        if session_id:
            print(f"✅ Session initialized: {session_id}")
        else:
            print("❌ Session initialization failed")
            return
        
        # Test 1: List available tools
        print("\n[Test 1] Listing available tools...")
        tools = await client.list_tools()
        if tools:
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                desc = tool.get('description', 'No description').replace('\n', ' ')[:80]
                print(f"  - {tool.get('name')}: {desc}...")
        else:
            print("❌ No tools found or error occurred")
        
        # Test 2: Simple calculation
        print("\n[Test 2] Testing calculate: 2 + 2")
        result = await client.calculate("2 + 2")
        if result is not None:
            print(f"✅ Result: {result}")
        else:
            print("❌ Calculation failed")
        
        # Test 3: Complex calculation
        print("\n[Test 3] Testing calculate: (10 * 5) + (20 / 4)")
        result = await client.calculate("(10 * 5) + (20 / 4)")
        if result is not None:
            print(f"✅ Result: {result}")
        else:
            print("❌ Calculation failed")
        
        # Test 4: Get weather
        print("\n[Test 4] Testing get_weather: Seoul")
        weather = await client.get_weather("Seoul")
        if weather:
            print(f"✅ Weather: {json.dumps(weather, indent=2)}")
        else:
            print("❌ Weather request failed")
        
        # Test 5: Get current time
        print("\n[Test 5] Testing get_current_time")
        time_info = await client.get_current_time()
        if time_info:
            print(f"✅ Time: {json.dumps(time_info, indent=2)}")
        else:
            print("❌ Time request failed")
        
        # Test 6: Generate random number
        print("\n[Test 6] Testing generate_random_number: 1-100")
        random_num = await client.generate_random_number(1, 100)
        if random_num is not None:
            print(f"✅ Random number: {random_num}")
        else:
            print("❌ Random number generation failed")
        
        # Test 7: Generate random number with custom range
        print("\n[Test 7] Testing generate_random_number: 1000-9999")
        random_num = await client.generate_random_number(1000, 9999)
        if random_num is not None:
            print(f"✅ Random number: {random_num}")
        else:
            print("❌ Random number generation failed")
        
        print("\n" + "=" * 60)
        print("Test suite completed")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()


async def interactive_mode():
    """Run the client in interactive mode."""
    client = MCPClient()
    
    print("=" * 60)
    print("MCP Client - Interactive Mode")
    print("=" * 60)
    
    # Initialize session
    session_id = await client.initialize()
    if not session_id:
        print("❌ Failed to initialize session")
        return
    
    print(f"✅ Session initialized: {session_id}")
    print("\nCommands:")
    print("  calc <expression>    - Calculate a mathematical expression")
    print("  weather <city>       - Get weather for a city")
    print("  time                 - Get current time")
    print("  random [min] [max]   - Generate random number (default: 1-100)")
    print("  tools                - List available tools")
    print("  exit                 - Exit interactive mode")
    print()
    
    try:
        while True:
            try:
                command = input(">>> ").strip()
                
                if not command:
                    continue
                
                if command == "exit":
                    print("Goodbye!")
                    break
                
                parts = command.split(maxsplit=1)
                cmd = parts[0].lower()
                
                if cmd == "calc" and len(parts) == 2:
                    result = await client.calculate(parts[1])
                    if result is not None:
                        print(f"Result: {result}")
                    else:
                        print("Calculation failed")
                
                elif cmd == "weather" and len(parts) == 2:
                    weather = await client.get_weather(parts[1])
                    if weather:
                        print(json.dumps(weather, indent=2))
                    else:
                        print("Weather request failed")
                
                elif cmd == "time":
                    time_info = await client.get_current_time()
                    if time_info:
                        print(json.dumps(time_info, indent=2))
                    else:
                        print("Time request failed")
                
                elif cmd == "random":
                    if len(parts) == 2:
                        range_parts = parts[1].split()
                        min_val = int(range_parts[0]) if len(range_parts) > 0 else 1
                        max_val = int(range_parts[1]) if len(range_parts) > 1 else 100
                    else:
                        min_val, max_val = 1, 100
                    
                    result = await client.generate_random_number(min_val, max_val)
                    if result is not None:
                        print(f"Random number: {result}")
                    else:
                        print("Random number generation failed")
                
                elif cmd == "tools":
                    tools = await client.list_tools()
                    if tools:
                        print(f"Available tools ({len(tools)}):")
                        for tool in tools:
                            desc = tool.get('description', 'No description').replace('\n', ' ')[:80]
                            print(f"  - {tool.get('name')}: {desc}...")
                    else:
                        print("No tools found")
                
                else:
                    print("Unknown command. Type 'exit' to quit.")
            
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except Exception as e:
                print(f"Error: {e}")
    
    finally:
        await client.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        asyncio.run(interactive_mode())
    else:
        asyncio.run(test_client())
