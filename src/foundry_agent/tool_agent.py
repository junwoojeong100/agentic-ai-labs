"""
Tool Agent - Uses MCP Server for various utility functions via Direct Client
"""

import logging
import os
from typing import Optional, List, Dict, Any
import json
import httpx
import re

from azure.ai.projects import AIProjectClient

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
            # Headers required by FastMCP server
            headers = {
                "Accept": "application/json, text/event-stream"
            }
            
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
                
                # Extract session ID from response headers
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
                
                # Send initialized notification (required by MCP protocol)
                initialized_notification = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                    "params": {}
                }
                
                response = await client.post(self.mcp_endpoint, json=initialized_notification, headers=headers)
                # Notification may return 204 No Content or 200, both are OK
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
                
                # Log response for debugging
                if response.status_code != 200:
                    logger.error(f"❌ tools/list failed with status {response.status_code}")
                    logger.error(f"   Response: {response.text}")
                
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
            # Headers required by FastMCP server (including session ID)
            headers = {
                "Accept": "application/json, text/event-stream"
            }
            
            # Add session ID if available
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


class ToolAgent:
    """
    Specialized agent that uses external tools via direct MCP client.
    This agent makes direct HTTP calls to the MCP server instead of relying
    on Azure's MCP Connector (which requires publicly accessible endpoints).
    """
    
    def __init__(
        self,
        project_client: AIProjectClient,
        mcp_endpoint: Optional[str] = None
    ):
        """
        Initialize the Tool Agent.
        
        Args:
            project_client: AIProjectClient instance
            mcp_endpoint: Optional MCP server endpoint (e.g., http://localhost:8000)
        """
        self.project_client = project_client
        self.mcp_endpoint = mcp_endpoint
        self.agent_id: Optional[str] = None
        self.mcp_client: Optional[MCPClient] = None
        
        self.name = "Tool Agent"
        # Get model deployment name from environment variable (default: gpt-5)
        self.model = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-5")
        
        # Create direct MCP client if endpoint is provided
        if mcp_endpoint:
            logger.info(f"Initializing direct MCP client with URL: {mcp_endpoint}")
            self.mcp_client = MCPClient(mcp_endpoint)
            
            self.instructions = """You are a specialized agent that uses external tools via MCP (Model Context Protocol).

You have access to the following MCP tools:
- get_weather: Get current weather for a city (requires "location" parameter with city name)

When a user asks a question:
1. Determine if you need to call a tool
2. If yes, respond ONLY with a JSON object in this exact format:
   {"tool": "tool_name", "arguments": {"arg1": "value1", "arg2": "value2"}}
3. If no tool is needed, respond normally

Examples:
- User: "서울 날씨를 알려주세요" → {"tool": "get_weather", "arguments": {"location": "Seoul"}}

IMPORTANT: 
- get_weather requires "location" (NOT "city")

Always respond in Korean when the user writes in Korean."""
        else:
            self.instructions = """You are a specialized agent that can use external tools.

Note: MCP server is not yet deployed. Please inform the user that tools are not available."""
    
    async def create(self) -> str:
        """Create the agent in Azure AI Foundry and initialize MCP client."""
        logger.info(f"Creating agent: {self.name}")
        
        try:
            # Initialize MCP client first
            if self.mcp_client:
                logger.info("Initializing MCP client...")
                success = await self.mcp_client.initialize()
                if not success:
                    logger.error("❌ Failed to initialize MCP client")
                    raise Exception("MCP client initialization failed")
            
            # Create agent (no tools registered with Azure, we handle them directly)
            agent = self.project_client.agents.create_agent(
                model=self.model,
                name=self.name,
                instructions=self.instructions
            )
            
            self.agent_id = agent.id
            logger.info(f"✅ Created {self.name}: {self.agent_id}")
            return self.agent_id
            
        except Exception as e:
            logger.error(f"❌ Failed to create agent: {e}")
            raise
    
    async def delete(self):
        """Delete the agent from Azure AI Foundry."""
        if self.agent_id:
            logger.info(f"Deleting agent: {self.name} ({self.agent_id})")
            self.project_client.agents.delete_agent(self.agent_id)
            self.agent_id = None
            logger.info(f"✅ Deleted {self.name}")
    
    def get_connected_tool(self):
        """Return this agent as a ConnectedAgentTool for use in Main Agent."""
        from azure.ai.agents.models import ConnectedAgentTool
        
        if not self.agent_id:
            raise ValueError("Agent must be created before getting connected tool")
        
        return ConnectedAgentTool(
            id=self.agent_id,
            name="tool_agent",
            description="""Use this agent for:
- Weather queries (e.g., 'What's the weather in Seoul?')

This agent has access to MCP (Model Context Protocol) tools and can execute real-time operations."""
        )
    
    def get_id(self) -> Optional[str]:
        """Get the agent ID."""
        return self.agent_id
    
    async def run(self, message: str, thread_id: Optional[str] = None) -> str:
        """
        Run the tool agent with a message.
        
        Args:
            message: User message
            thread_id: Optional thread ID for conversation continuity
            
        Returns:
            Agent response
        """
        import time
        
        try:
            # ========================================================================
            # 🔍 OpenTelemetry Span for Tool Agent Execution Tracing
            # ========================================================================
            from opentelemetry import trace
            tracer = trace.get_tracer(__name__)
            
            with tracer.start_as_current_span("tool_agent_run") as span:
                # Gen AI semantic conventions
                span.set_attribute("gen_ai.system", "azure_ai_agent")
                span.set_attribute("gen_ai.request.model", self.model)
                span.set_attribute("gen_ai.prompt", message)
                span.set_attribute("agent.id", self.agent_id)
                span.set_attribute("agent.name", self.name)
                span.set_attribute("agent.type", "tool_agent")
                
                # Create thread
                thread = self.project_client.agents.threads.create()
                logger.info(f"[thread] {thread.id}")
                span.set_attribute("thread.id", thread.id)
            
                # Add user message
                self.project_client.agents.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=message
                )
                logger.info(f"[message] User message added to thread")
                
                # Create and process run
                run = self.project_client.agents.runs.create_and_process(
                    thread_id=thread.id,
                    agent_id=self.agent_id
                )
                logger.info(f"[run] {run.id} status={run.status}")
                span.set_attribute("run.id", run.id)
                span.set_attribute("run.status", run.status)
            
            # Check for errors
            if run.status == "failed":
                error_msg = "Run failed"
                if hasattr(run, 'last_error') and run.last_error:
                    logger.error(f"[run] ❌ Run failed with error: {run.last_error}")
                    error_msg = f"Run failed: {run.last_error}"
                return error_msg
            
            # Get the LLM's response
            messages = self.project_client.agents.messages.list(thread_id=thread.id)
            
            response_text = None
            for m in messages:
                role = m.get('role') if isinstance(m, dict) else getattr(m, 'role', 'unknown')
                
                if role == 'assistant':
                    content_items = m.get('content', []) if isinstance(m, dict) else getattr(m, 'content', [])
                    
                    for item in content_items:
                        if isinstance(item, dict) and 'text' in item:
                            text_value = item['text']
                            if isinstance(text_value, dict) and 'value' in text_value:
                                response_text = text_value['value']
                            else:
                                response_text = str(text_value)
                            break
                        elif hasattr(item, 'text'):
                            text_obj = item.text
                            if hasattr(text_obj, 'value'):
                                response_text = text_obj.value
                            else:
                                response_text = str(text_obj)
                            break
                    
                
                if response_text:
                    # Log output to span for Tracing UI
                    span.set_attribute("gen_ai.completion", response_text)
                    span.set_attribute("gen_ai.response.finish_reason", "stop")
                    break
            
            if not response_text:
                logger.warning("No assistant response found")
                return "No response generated"
            
            logger.info(f"[llm] Response: {response_text[:200]}...")
            
            # Check if LLM wants to call a tool
            logger.info(f"[tool] Checking for tool calls. MCP client available: {self.mcp_client is not None}")
            
            if self.mcp_client:
                tool_call = self._parse_tool_call(response_text)
                
                logger.info(f"[tool] Parsed tool call: {tool_call}")
                
                if tool_call:
                    tool_name = tool_call['tool']
                    arguments = tool_call['arguments']
                    
                    logger.info(f"[tool] LLM requested tool call: {tool_name}")
                    
                    # Call the MCP tool directly
                    tool_result = await self.mcp_client.call_tool(tool_name, arguments)
                    
                    # Parse tool result (handle both dict and string)
                    if isinstance(tool_result, dict):
                        result_str = json.dumps(tool_result, ensure_ascii=False, indent=2)
                    else:
                        result_str = str(tool_result)
                    
                    # Format the result in Korean
                    if tool_name == "get_weather":
                        final_response = f"날씨 정보: {result_str}"
                    else:
                        final_response = result_str
                    
                    logger.info(f"[result] {final_response}")
                    return final_response
            
            # No tool call, return LLM response directly
            return response_text
            
        except Exception as e:
            logger.error(f"Error running tool agent: {e}", exc_info=True)
            raise
    
    def _parse_tool_call(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse tool call from LLM response.
        
        Args:
            response: LLM response text
            
        Returns:
            Dict with 'tool' and 'arguments' keys, or None if no tool call
        """
        try:
            # First try: parse entire response as JSON
            response_stripped = response.strip()
            if response_stripped.startswith('{') and response_stripped.endswith('}'):
                tool_call = json.loads(response_stripped)
                if 'tool' in tool_call and 'arguments' in tool_call:
                    logger.info(f"[parse] Found tool call: {tool_call}")
                    return tool_call
            
            # Second try: find JSON pattern in response
            # Look for {"tool": "...", "arguments": {...}}
            json_match = re.search(r'\{[^}]*"tool"[^}]*"arguments"[^}]*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                # Try to balance braces for nested objects
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
            logger.debug(f"[parse] No tool call found in response: {e}")
            return None
