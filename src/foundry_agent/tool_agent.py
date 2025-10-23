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
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any], max_retries: int = 3) -> Any:
        """
        Call an MCP tool with retry logic and session recovery.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments as a dictionary
            max_retries: Maximum number of retry attempts (default: 3)
            
        Returns:
            Tool result
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Session recovery: Reinitialize on retry attempts
                if attempt > 0:
                    logger.warning(f"🔄 Retry {attempt + 1}/{max_retries}: Reinitializing MCP session...")
                    reinit_success = await self.initialize()
                    if not reinit_success:
                        logger.error(f"❌ Failed to reinitialize MCP session")
                        # Continue with existing session
                
                # Headers required by FastMCP server (including session ID)
                headers = {
                    "Accept": "application/json, text/event-stream"
                }
                
                # Add session ID if available
                if self.session_id:
                    headers['mcp-session-id'] = self.session_id
                
                # Increase timeout to 60 seconds for external API calls
                async with httpx.AsyncClient(timeout=60.0) as client:
                    call_request = {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {
                            "name": tool_name,
                            "arguments": arguments
                        }
                    }
                    
                    if attempt > 0:
                        logger.info(f"🔁 Retry attempt {attempt + 1}/{max_retries} for tool: {tool_name}")
                    else:
                        logger.info(f"🔧 Calling MCP tool: {tool_name} with args: {arguments}")
                    
                    response = await client.post(self.mcp_endpoint, json=call_request, headers=headers)
                    response.raise_for_status()
                    
                    # Parse SSE response
                    content = response.text
                    for line in content.split('\n'):
                        if line.startswith('data: '):
                            data = json.loads(line[6:])
                            
                            # Check for MCP errors
                            if 'error' in data:
                                error_msg = data['error'].get('message', 'Unknown error')
                                logger.warning(f"⚠️  MCP error: {error_msg}")
                                if 'session' in error_msg.lower() and attempt < max_retries - 1:
                                    raise Exception(f"Session error: {error_msg}")
                            
                            if 'result' in data:
                                result = data['result']
                                logger.info(f"✅ Tool result (attempt {attempt + 1}): {result}")
                                
                                # Extract content from MCP response format
                                if isinstance(result, dict) and 'content' in result:
                                    content_items = result['content']
                                    if isinstance(content_items, list) and len(content_items) > 0:
                                        first_item = content_items[0]
                                        if isinstance(first_item, dict) and 'text' in first_item:
                                            return first_item['text']
                                
                                return result
                    
                    return None
                    
            except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadTimeout) as e:
                last_error = e
                logger.warning(f"⚠️  MCP timeout/connection error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                continue
                
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                
                # Retry on session errors
                if 'session' in error_msg and attempt < max_retries - 1:
                    logger.warning(f"⚠️  Session error (attempt {attempt + 1}/{max_retries}): {e}")
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    logger.error(f"❌ Failed to call tool {tool_name}: {e}")
                    raise
        
        # All retries failed
        logger.error(f"❌ All {max_retries} retry attempts failed for tool {tool_name}")
        raise Exception(f"MCP call failed after {max_retries} attempts: {last_error}")
    
    async def close(self):
        """Clean up MCP client resources."""
        # MCPClient uses httpx.AsyncClient which is created and closed in context managers
        # No persistent connections to clean up, but we can clear session state
        if self.session_id:
            logger.debug(f"Clearing MCP session: {self.session_id}")
            self.session_id = None
        self.available_tools.clear()
        logger.debug("MCPClient cleanup completed")


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
            
            self.instructions = """CRITICAL: You MUST follow these rules exactly.

When user asks about weather:
1. Return ONLY this JSON format (no other text, no explanation):
{"tool": "get_weather", "arguments": {"location": "CityName"}}

2. City name conversion:
- 서울 → Seoul
- 부산 → Busan  
- 제주 → Jeju
- 인천 → Incheon

3. EXAMPLES - Copy this format EXACTLY:

User: "서울 날씨"
You: {"tool": "get_weather", "arguments": {"location": "Seoul"}}

User: "서울의 현재 날씨를 알려주세요. 온도와 체감온도, 날씨 상태, 습도, 바람 정보를 모두 포함해주세요."
You: {"tool": "get_weather", "arguments": {"location": "Seoul"}}

User: "Tokyo weather"
You: {"tool": "get_weather", "arguments": {"location": "Tokyo"}}

4. For non-weather questions, answer normally in Korean.

REMEMBER: Weather questions = JSON ONLY. No text before or after the JSON."""
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
        """Delete the agent from Azure AI Foundry and clean up resources."""
        logger.info(f"Cleaning up {self.name}...")
        
        # Clean up MCP client first
        if self.mcp_client:
            try:
                await self.mcp_client.close()
                self.mcp_client = None
                logger.info("✅ MCP client cleaned up")
            except Exception as e:
                logger.warning(f"⚠️  Error cleaning up MCP client: {e}")
        
        # Delete agent from Azure
        if self.agent_id:
            try:
                logger.info(f"Deleting agent: {self.name} ({self.agent_id})")
                self.project_client.agents.delete_agent(self.agent_id)
                self.agent_id = None
                logger.info(f"✅ Deleted {self.name}")
            except Exception as e:
                logger.warning(f"⚠️  Error deleting agent: {e}")
        
        logger.info(f"✅ Cleanup completed for {self.name}")
    
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
    
    async def run(self, user_query: str, thread_name: Optional[str] = None) -> str:
        """
        Run agent to execute user query.
        
        Args:
            user_query: User's input query
            thread_name: Optional thread name for conversation context
            
        Returns:
            Agent's response
        """
        # ALWAYS re-initialize MCP session for each run to avoid stale session issues
        if self.mcp_client:
            logger.info("🔄 Re-initializing MCP session for new request...")
            reinit_success = await self.mcp_client.initialize()
            if not reinit_success:
                logger.error("❌ Failed to initialize MCP session")
                return "MCP 서버에 연결할 수 없습니다."
        
        thread = None
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
            
                # Check if this is a weather-related query
                weather_keywords = ['날씨', 'weather', '기온', '온도', 'temperature', '습도', 'humidity', '바람', 'wind']
                is_weather_query = any(keyword in message.lower() for keyword in weather_keywords)
                
                # If weather query, add explicit JSON instruction to the message
                if is_weather_query and self.mcp_client:
                    enhanced_message = f"""{message}

[IMPORTANT: Return tool call in JSON format: {{"tool": "get_weather", "arguments": {{"location": "CityName"}}}}]"""
                    logger.info(f"[weather_query] Enhanced message with JSON instruction")
                else:
                    enhanced_message = message
                
                # Add user message
                self.project_client.agents.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=enhanced_message
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
                
                # If no tool call detected but user asked about weather, force retry
                if not tool_call and any(keyword in user_query.lower() for keyword in ['날씨', '기온', '온도', 'weather', 'temperature']):
                    logger.warning(f"[tool] ⚠️ Weather query detected but no tool call! Response: {response_text[:200]}")
                    logger.warning(f"[tool] LLM failed to generate tool call JSON. Retrying with explicit instruction...")
                    
                    # Send explicit reminder
                    retry_prompt = f"""CRITICAL: You MUST call the get_weather tool. Return ONLY this JSON:
{{"tool": "get_weather", "arguments": {{"location": "Seoul"}}}}

Original query: {user_query}"""
                    
                    self.project_client.agents.messages.create(
                        thread_id=thread.id,
                        role="user",
                        content=retry_prompt
                    )
                    
                    run_retry = self.project_client.agents.runs.create_and_process(
                        thread_id=thread.id,
                        agent_id=self.agent_id
                    )
                    
                    messages_retry = self.project_client.agents.messages.list(thread_id=thread.id)
                    for m in list(messages_retry):
                        role = m.get('role') if isinstance(m, dict) else getattr(m, 'role', 'unknown')
                        if role == 'assistant':
                            content_items = m.get('content', []) if isinstance(m, dict) else getattr(m, 'content', [])
                            for item in content_items:
                                if isinstance(item, dict) and 'text' in item:
                                    text_value = item['text']
                                    retry_text = text_value['value'] if isinstance(text_value, dict) else str(text_value)
                                elif hasattr(item, 'text'):
                                    retry_text = item.text.value if hasattr(item.text, 'value') else str(item.text)
                                
                                logger.info(f"[tool] Retry response: {retry_text[:200]}")
                                tool_call = self._parse_tool_call(retry_text)
                                if tool_call:
                                    logger.info(f"[tool] ✅ Retry successful! Tool call: {tool_call}")
                                    break
                            break
                
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
                    
                    logger.info(f"[tool_result] Received: {result_str}")
                    logger.info(f"[tool_result] Type: {type(tool_result)}, Length: {len(result_str)}")
                    logger.info(f"[tool_result] First 500 chars: {result_str[:500]}")
                    
                    # ====================================================================
                    # IMPORTANT: Send tool result back to LLM for proper formatting
                    # ====================================================================
                    # The LLM needs to see the actual data to format it properly
                    # instead of using placeholders
                    # ====================================================================
                    
                    # Create formatting prompt (same as Agent Framework)
                    format_prompt = f"""Tool '{tool_name}' returned the following result. Please present this ACTUAL data to the user in a clear, friendly format in Korean. DO NOT use placeholders:

{result_str}

Present the data clearly with all details."""
                    
                    logger.info(f"[format_prompt] Sending to LLM: {format_prompt[:300]}...")
                    
                    # Add tool result as a user message
                    self.project_client.agents.messages.create(
                        thread_id=thread.id,
                        role="user",
                        content=format_prompt
                    )
                    
                    # Run LLM again to format the tool result
                    run2 = self.project_client.agents.runs.create_and_process(
                        thread_id=thread.id,
                        agent_id=self.agent_id
                    )
                    logger.info(f"[run2] {run2.id} status={run2.status}")
                    
                    # Get the formatted response
                    messages2 = self.project_client.agents.messages.list(thread_id=thread.id)
                    
                    # Convert to list to get the latest message (list() returns newest first)
                    messages_list = list(messages2)
                    logger.info(f"[messages2] Total messages after formatting: {len(messages_list)}")
                    
                    formatted_response = None
                    # Get the FIRST (most recent) assistant message
                    for m in messages_list:
                        role = m.get('role') if isinstance(m, dict) else getattr(m, 'role', 'unknown')
                        
                        logger.info(f"[messages2] Checking message with role: {role}")
                        
                        if role == 'assistant':
                            content_items = m.get('content', []) if isinstance(m, dict) else getattr(m, 'content', [])
                            
                            for item in content_items:
                                if isinstance(item, dict) and 'text' in item:
                                    text_value = item['text']
                                    if isinstance(text_value, dict) and 'value' in text_value:
                                        formatted_response = text_value['value']
                                    else:
                                        formatted_response = str(text_value)
                                    break
                                elif hasattr(item, 'text'):
                                    text_obj = item.text
                                    if hasattr(text_obj, 'value'):
                                        formatted_response = text_obj.value
                                    else:
                                        formatted_response = str(text_obj)
                                    break
                            
                            if formatted_response:
                                logger.info(f"[formatted] Found formatted response (length: {len(formatted_response)})")
                                logger.info(f"[formatted] Content: {formatted_response[:300]}...")
                                return formatted_response
                    
                    # Fallback: return raw tool result if formatting failed
                    logger.warning("[formatted] Failed to get formatted response, returning raw tool result")
                    if tool_name == "get_weather":
                        return f"날씨 정보:\n{result_str}"
                    return result_str
            
            # No tool call, return LLM response directly
            return response_text
            
        except Exception as e:
            logger.error(f"Error running tool agent: {e}", exc_info=True)
            raise
        finally:
            # Clean up thread to prevent resource leaks
            if thread:
                try:
                    self.project_client.agents.threads.delete(thread.id)
                    logger.debug(f"Thread {thread.id} deleted")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to delete thread {thread.id}: {cleanup_error}")
    
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
