"""
Tool Agent - Microsoft Agent Framework Implementation
Uses MCP Server for various utility functions
"""

import asyncio
import logging
import json
import re
import httpx
from typing import Optional, List, Dict, Any, Annotated

from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import AzureCliCredential, ManagedIdentityCredential, ChainedTokenCredential

logger = logging.getLogger(__name__)


class MCPClient:
    """Direct MCP client for calling MCP server tools."""
    
    def __init__(self, server_url: str):
        """
        Initialize MCP client.
        
        Args:
            server_url: Base URL of MCP server (e.g., http://localhost:8000)
        """
        self.server_url = server_url.rstrip('/')
        self.mcp_endpoint = f"{self.server_url}/mcp"
        self.session_id: Optional[str] = None
        self.available_tools: List[Dict[str, Any]] = []
        
    async def initialize(self) -> bool:
        """Initialize MCP session and discover tools."""
        try:
            headers = {"Accept": "application/json, text/event-stream"}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Initialize session
                init_request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "tool-agent-client",
                            "version": "1.0.0"
                        }
                    }
                }
                
                response = await client.post(self.mcp_endpoint, json=init_request, headers=headers)
                response.raise_for_status()
                
                # Extract session ID
                session_id = response.headers.get('mcp-session-id')
                if session_id:
                    self.session_id = session_id
                    headers['mcp-session-id'] = session_id
                    logger.info(f"✅ MCP session initialized with ID: {session_id}")
                
                # Parse SSE response
                content = response.text
                for line in content.split('\n'):
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        if 'result' in data:
                            logger.info(f"✅ Initialize result: {data['result']}")
                            break
                
                # Send initialized notification
                initialized_notification = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                    "params": {}
                }
                
                response = await client.post(self.mcp_endpoint, json=initialized_notification, headers=headers)
                if response.status_code not in [200, 204]:
                    response.raise_for_status()
                logger.info("✅ Sent initialized notification")
                
                # List available tools
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }
                
                response = await client.post(self.mcp_endpoint, json=tools_request, headers=headers)
                response.raise_for_status()
                
                # Parse tools from SSE response
                content = response.text
                for line in content.split('\n'):
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        if 'result' in data and 'tools' in data['result']:
                            self.available_tools = data['result']['tools']
                            logger.info(f"✅ Discovered {len(self.available_tools)} MCP tools")
                            for tool in self.available_tools:
                                logger.info(f"   - {tool['name']}: {tool.get('description', 'No description')}")
                            return True
                
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize MCP client: {e}")
            return False
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call an MCP tool.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments as a dictionary
            
        Returns:
            Tool result
        """
        try:
            headers = {"Accept": "application/json, text/event-stream"}
            
            if self.session_id:
                headers['mcp-session-id'] = self.session_id
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                call_request = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }
                
                logger.info(f"🔧 Calling MCP tool: {tool_name} with args: {arguments}")
                
                response = await client.post(self.mcp_endpoint, json=call_request, headers=headers)
                response.raise_for_status()
                
                # Parse SSE response
                content = response.text
                for line in content.split('\n'):
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        if 'result' in data:
                            result = data['result']
                            logger.info(f"✅ Tool result: {result}")
                            
                            # Extract content from MCP response format
                            if isinstance(result, dict) and 'content' in result:
                                content_items = result['content']
                                if isinstance(content_items, list) and len(content_items) > 0:
                                    first_item = content_items[0]
                                    if isinstance(first_item, dict) and 'text' in first_item:
                                        return first_item['text']
                            
                            return result
                
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to call tool {tool_name}: {e}")
            raise
    
    async def close(self):
        """Clean up MCP client resources."""
        # MCPClient uses httpx.AsyncClient which is created and closed in context managers
        # No persistent connections to clean up
        logger.debug("MCPClient cleanup completed")


class ToolAgent:
    """
    Specialized agent that uses external tools via MCP.
    Uses Microsoft Agent Framework with custom tool integration.
    """
    
    def __init__(
        self,
        project_endpoint: Optional[str] = None,
        model_deployment_name: Optional[str] = None,
        mcp_endpoint: Optional[str] = None
    ):
        """
        Initialize the Tool Agent.
        
        Args:
            project_endpoint: Azure AI Project endpoint
            model_deployment_name: Model deployment name
            mcp_endpoint: Optional MCP server endpoint
        """
        self.project_endpoint = project_endpoint
        self.model_deployment_name = model_deployment_name or "gpt-4o"
        self.mcp_endpoint = mcp_endpoint
        
        self.agent: Optional[ChatAgent] = None
        self.credential: Optional[ChainedTokenCredential] = None
        self.chat_client: Optional[AzureAIAgentClient] = None
        self.mcp_client: Optional[MCPClient] = None
        
        self.name = "Tool Agent"
        
        # Create MCP client if endpoint is provided
        if mcp_endpoint:
            logger.info(f"Initializing MCP client with URL: {mcp_endpoint}")
            self.mcp_client = MCPClient(mcp_endpoint)
            
            self.instructions = """You are a specialized agent that uses external tools via MCP.

You have access to the following MCP tools:
- get_weather: Get current weather for a city (requires "location" parameter)
- calculate: Perform calculations (requires "expression" parameter)
- get_current_time: Get current date and time (no parameters)
- generate_random_number: Generate random numbers (requires "min" and "max" as integers)

When a user asks a question:
1. Determine if you need to call a tool
2. If yes, respond ONLY with JSON: {"tool": "tool_name", "arguments": {...}}
3. If no tool needed, respond normally

Examples:
- "2 + 2는?" → {"tool": "calculate", "arguments": {"expression": "2 + 2"}}
- "서울 날씨?" → {"tool": "get_weather", "arguments": {"location": "Seoul"}}
- "지금 몇 시?" → {"tool": "get_current_time", "arguments": {}}

Always respond in Korean when user writes in Korean."""
        else:
            self.instructions = "You are a helpful assistant. MCP tools are not available."
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
    
    async def initialize(self):
        """Initialize the agent and MCP client."""
        logger.info(f"Initializing {self.name}")
        
        # Initialize MCP client first
        if self.mcp_client:
            logger.info("Initializing MCP client...")
            success = await self.mcp_client.initialize()
            if not success:
                logger.error("❌ Failed to initialize MCP client")
                raise Exception("MCP client initialization failed")
        
        # Create credential chain: Try Managed Identity first (for Container Apps), then Azure CLI (for local dev)
        self.credential = ChainedTokenCredential(
            ManagedIdentityCredential(),
            AzureCliCredential()
        )
        
        # Create Azure AI Agent Client
        self.chat_client = AzureAIAgentClient(
            project_endpoint=self.project_endpoint,
            model_deployment_name=self.model_deployment_name,
            async_credential=self.credential,
        )
        
        # Create the agent (create_agent is not async)
        self.agent = self.chat_client.create_agent(
            name=self.name,
            instructions=self.instructions
        )
        
        logger.info(f"✅ Initialized {self.name}")
    
    async def cleanup(self):
        """Clean up resources."""
        logger.info(f"Cleaning up {self.name}")
        
        if self.agent:
            self.agent = None
        
        if self.chat_client:
            await self.chat_client.close()
            self.chat_client = None
        
        if self.mcp_client:
            await self.mcp_client.close()
            self.mcp_client = None
        
        if self.credential:
            await self.credential.close()
            self.credential = None
        
        # Give time for connections to close properly
        await asyncio.sleep(0.1)
        
        logger.info(f"✅ Cleaned up {self.name}")
    
    async def run(self, message: str, thread=None) -> str:
        """
        Run the tool agent with a message.
        
        Args:
            message: User message
            thread: Optional thread for conversation continuity
            
        Returns:
            Agent response text
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized")
        
        try:
            logger.info(f"Running {self.name} with message: {message[:100]}...")
            
            # Get LLM response
            result = await self.agent.run(message, thread=thread)
            response_text = result.text if hasattr(result, 'text') else str(result)
            
            logger.info(f"[llm] Response: {response_text[:200]}...")
            
            # Check if LLM wants to call a tool
            if self.mcp_client:
                tool_call = self._parse_tool_call(response_text)
                
                if tool_call:
                    tool_name = tool_call['tool']
                    arguments = tool_call['arguments']
                    
                    logger.info(f"[tool] Calling: {tool_name}")
                    
                    # Call the MCP tool
                    tool_result = await self.mcp_client.call_tool(tool_name, arguments)
                    
                    # Format result in Korean
                    if isinstance(tool_result, dict):
                        result_str = json.dumps(tool_result, ensure_ascii=False, indent=2)
                    else:
                        result_str = str(tool_result)
                    
                    if tool_name == "calculate":
                        final_response = f"계산 결과: {result_str}"
                    elif tool_name == "get_weather":
                        final_response = f"날씨 정보: {result_str}"
                    elif tool_name == "get_current_time":
                        final_response = f"현재 시간: {result_str}"
                    elif tool_name == "generate_random_number":
                        final_response = f"생성된 랜덤 숫자: {result_str}"
                    else:
                        final_response = result_str
                    
                    logger.info(f"[result] {final_response}")
                    return final_response
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error running tool agent: {e}", exc_info=True)
            raise
    
    def _parse_tool_call(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse tool call from LLM response."""
        try:
            # Try parsing entire response as JSON
            response_stripped = response.strip()
            if response_stripped.startswith('{') and response_stripped.endswith('}'):
                tool_call = json.loads(response_stripped)
                if 'tool' in tool_call and 'arguments' in tool_call:
                    logger.info(f"[parse] Found tool call: {tool_call}")
                    return tool_call
            
            # Try finding JSON pattern
            json_match = re.search(r'\{[^}]*"tool"[^}]*"arguments"[^}]*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                brace_count = 0
                end_pos = 0
                for i, char in enumerate(json_str):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_pos = i + 1
                            break
                
                if end_pos > 0:
                    json_str = json_str[:end_pos]
                
                tool_call = json.loads(json_str)
                
                if 'tool' in tool_call and 'arguments' in tool_call:
                    logger.info(f"[parse] Found tool call: {tool_call}")
                    return tool_call
            
            return None
            
        except Exception as e:
            logger.debug(f"[parse] No tool call found: {e}")
            return None
    
    def get_new_thread(self):
        """Create a new conversation thread."""
        if not self.agent:
            raise RuntimeError("Agent not initialized")
        return self.agent.get_new_thread()
