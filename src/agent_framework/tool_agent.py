"""
Tool Agent - Microsoft Agent Framework Implementation
Uses MCP Server for various utility functions
"""

import asyncio
import logging
import os
import json
import re
import httpx
from typing import Optional, List, Dict, Any, Annotated

from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import AzureCliCredential, ManagedIdentityCredential, ChainedTokenCredential

# OpenTelemetry imports for tracing
from opentelemetry import trace

# Import masking utility
from masking import mask_content

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
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any], max_retries: int = 3) -> Any:
        """
        Call an MCP tool with retry logic and automatic session recovery.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments as a dictionary
            max_retries: Maximum number of retry attempts (default: 3)
            
        Returns:
            Tool result
        """
        last_error = None
        session_reinitialized = False
        
        for attempt in range(max_retries):
            try:
                # Session validation and reinitialization on retry
                if attempt > 0 and not session_reinitialized:
                    logger.warning(f"🔄 Reinitializing MCP session before retry {attempt + 1}/{max_retries}")
                    reinit_success = await self.initialize()
                    if reinit_success:
                        logger.info(f"✅ MCP session reinitialized successfully")
                        session_reinitialized = True
                    else:
                        logger.error(f"❌ Failed to reinitialize MCP session")
                        # Continue anyway to try with existing session
                
                headers = {"Accept": "application/json, text/event-stream"}
                
                if self.session_id:
                    headers['mcp-session-id'] = self.session_id
                
                # Increase timeout to 60 seconds
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
                            
                            # Check for MCP errors (session expired, etc.)
                            if 'error' in data:
                                error_msg = data['error'].get('message', 'Unknown error')
                                error_code = data['error'].get('code', 0)
                                logger.warning(f"⚠️  MCP error: {error_msg} (code: {error_code})")
                                
                                # Session-related errors should trigger reinitialization
                                if 'session' in error_msg.lower() or error_code in [-32000, -32001]:
                                    if attempt < max_retries - 1:
                                        logger.info(f"🔄 Session error detected, will reinitialize on next attempt")
                                        raise Exception(f"Session error: {error_msg}")
                                    else:
                                        raise Exception(f"MCP session error: {error_msg}")
                            
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
                logger.warning(f"⚠️  MCP call timeout/connection error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    import asyncio
                    await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff: 1s, 2s, 3s
                continue
                
            except httpx.HTTPStatusError as e:
                last_error = e
                # Check for session-related HTTP errors (400, 401, 403)
                if e.response.status_code in [400, 401, 403]:
                    logger.warning(f"⚠️  HTTP {e.response.status_code} error (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        import asyncio
                        await asyncio.sleep(1 * (attempt + 1))
                    continue
                else:
                    logger.error(f"❌ HTTP error calling tool {tool_name}: {e}")
                    raise
                
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                
                # Check if error is session-related
                if 'session' in error_msg and attempt < max_retries - 1:
                    logger.warning(f"⚠️  Session error (attempt {attempt + 1}/{max_retries}): {e}")
                    import asyncio
                    await asyncio.sleep(1 * (attempt + 1))
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
        # Priority: Parameter > Environment variable > Default fallback
        if model_deployment_name:
            self.model_deployment_name = model_deployment_name
        else:
            self.model_deployment_name = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME")
            if not self.model_deployment_name:
                logger.warning(
                    "AZURE_AI_MODEL_DEPLOYMENT_NAME not set. "
                    "Using 'gpt-5' as fallback."
                )
                self.model_deployment_name = "gpt-5"
        
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

🔧 Available MCP Tools:
- get_weather: Get current weather for a city (requires "location" parameter)

📋 How to use tools:
1. Analyze the user's question
2. If the question requires a tool (e.g., weather query), respond with ONLY this JSON format:
   {"tool": "tool_name", "arguments": {"param": "value"}}
3. If no tool is needed, respond naturally in the user's language

✅ Examples:
- User: "서울 날씨?" → {"tool": "get_weather", "arguments": {"location": "Seoul"}}
- User: "What's the weather in Tokyo?" → {"tool": "get_weather", "arguments": {"location": "Tokyo"}}
- User: "뉴욕과 런던의 날씨 알려줘" → {"tool": "get_weather", "arguments": {"location": "New York"}}

⚠️ Important:
- For weather queries, ALWAYS use the tool (return JSON only)
- Match the user's language (Korean/English)
- Be precise with location names"""
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
        
        # ========================================================================
        # 🔍 OpenTelemetry Span for Tool Agent Execution Tracing
        # ========================================================================
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("tool_agent.execute") as span:
            span.set_attribute("agent.type", "tool")
            span.set_attribute("agent.message", mask_content(message))
            span.set_attribute("tool.mcp_endpoint", self.mcp_endpoint or "not_configured")
            
            try:
                logger.info(f"Running {self.name} with message: {message[:100]}...")
                
                # Create thread if not provided (same as research_agent)
                if thread is None:
                    thread = self.agent.get_new_thread()
                
                # Get LLM response with tracing
                with tracer.start_as_current_span("tool_agent.llm_call") as llm_span:
                    llm_span.set_attribute("gen_ai.system", "azure_ai_agent_framework")
                    llm_span.set_attribute("gen_ai.request.model", self.model_deployment_name)
                    llm_span.set_attribute("gen_ai.prompt", mask_content(message))
                    
                    result = await self.agent.run(message, thread=thread)
                    
                    # Extract response using the same logic as research_agent
                    response_text = None
                    
                    if hasattr(result, 'messages') and result.messages:
                        last_message = result.messages[-1]
                        
                        # Try to get from 'contents' attribute
                        if hasattr(last_message, 'contents') and last_message.contents:
                            try:
                                first_content = last_message.contents[0]
                                if hasattr(first_content, 'text'):
                                    response_text = first_content.text
                                elif hasattr(first_content, '__getattribute__'):
                                    try:
                                        response_text = getattr(first_content, 'text')
                                    except AttributeError:
                                        pass
                            except (IndexError, AttributeError, TypeError):
                                pass
                        
                        # Fallback: Try 'text' attribute on message
                        if not response_text and hasattr(last_message, 'text'):
                            response_text = last_message.text
                    
                    # Final fallback
                    if not response_text:
                        response_text = "No response"
                        logger.warning("No response extracted from tool agent LLM call")
                    
                    llm_span.set_attribute("gen_ai.completion", mask_content(response_text))
                    llm_span.set_attribute("gen_ai.response.length", len(response_text))
                
                logger.info(f"[llm] Response: {response_text[:200]}...")
                
                # Check if LLM wants to call a tool
                if self.mcp_client:
                    tool_call = self._parse_tool_call(response_text)
                    
                    if tool_call:
                        tool_name = tool_call['tool']
                        arguments = tool_call['arguments']
                        
                        logger.info(f"[tool] Calling: {tool_name}")
                        
                        # Call the MCP tool with tracing
                        with tracer.start_as_current_span("tool_agent.mcp_call") as mcp_span:
                            mcp_span.set_attribute("mcp.tool_name", tool_name)
                            mcp_span.set_attribute("mcp.arguments", json.dumps(arguments))
                            
                            tool_result = await self.mcp_client.call_tool(tool_name, arguments)
                            
                            mcp_span.set_attribute("mcp.result", str(tool_result)[:500])
                        
                        # Format result in Korean
                        if isinstance(tool_result, dict):
                            result_str = json.dumps(tool_result, ensure_ascii=False, indent=2)
                        else:
                            result_str = str(tool_result)
                        
                        if tool_name == "get_weather":
                            final_response = f"날씨 정보: {result_str}"
                        else:
                            final_response = result_str
                        
                        span.set_attribute("tool.final_response_length", len(final_response))
                        span.set_attribute("tool.status", "success_with_tool_call")
                        
                        logger.info(f"[result] {final_response}")
                        return final_response
                
                span.set_attribute("tool.status", "success_no_tool_call")
                span.set_attribute("tool.response_length", len(response_text))
                
                return response_text
                
            except Exception as e:
                logger.error(f"Error running tool agent: {e}", exc_info=True)
                span.set_attribute("tool.status", "error")
                span.set_attribute("error.message", str(e))
                span.record_exception(e)
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
