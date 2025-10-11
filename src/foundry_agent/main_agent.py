"""
Main Agent - Coordinates between specialized agents
"""

import logging
import os
from typing import Optional

from azure.ai.projects import AIProjectClient

logger = logging.getLogger(__name__)


class MainAgent:
    """
    Main agent that coordinates task delegation between specialized agents.
    Uses Connected Agents to delegate to Tool Agent and Research Agent.
    """
    
    def __init__(self, project_client: AIProjectClient, connected_tools: list = None):
        """
        Initialize the Main Agent.
        
        Args:
            project_client: AIProjectClient instance
            connected_tools: List of ConnectedAgentTool instances (Tool Agent, Research Agent)
        """
        self.project_client = project_client
        self.agent_id: Optional[str] = None
        self.connected_tools = connected_tools or []
        
        # Get model deployment name from environment variable (default: gpt-4o)
        self.model = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4o")
        
        instructions = """You are the main agent that coordinates between specialized agents.

Your responsibilities:
1. Analyze user requests and determine which specialized agent to use
2. Delegate tasks to the appropriate connected agent:
   - Use 'tool_agent' for: weather queries, calculations, time/date, random numbers
   - Use 'research_agent' for: technical questions, best practices, documentation searches
3. You can use multiple agents if the question requires both tools and research
4. Synthesize responses from connected agents into a clear, comprehensive answer

Always choose the right agent(s) based on the user's question and provide well-structured responses."""
        
        self.name = "Main Agent"
        self.instructions = instructions
    
    def create(self) -> str:
        """Create the agent in Azure AI Foundry with Connected Agents."""
        logger.info(f"Creating agent: {self.name}")
        
        # Collect tool definitions from connected agents
        tools_definitions = []
        for connected_tool in self.connected_tools:
            tools_definitions.extend(connected_tool.definitions)
        
        # Create agent with connected tools
        if tools_definitions:
            agent = self.project_client.agents.create_agent(
                model=self.model,
                name=self.name,
                instructions=self.instructions,
                tools=tools_definitions
            )
            logger.info(f"✅ Created {self.name} with {len(self.connected_tools)} connected agents")
        else:
            agent = self.project_client.agents.create_agent(
                model=self.model,
                name=self.name,
                instructions=self.instructions
            )
            logger.info(f"✅ Created {self.name} (no connected agents)")
        
        self.agent_id = agent.id
        logger.info(f"✅ Created {self.name}: {self.agent_id}")
        return self.agent_id
    
    def delete(self):
        """Delete the agent."""
        if self.agent_id:
            logger.info(f"Deleting agent: {self.name} ({self.agent_id})")
            self.project_client.agents.delete_agent(self.agent_id)
            self.agent_id = None
            logger.info(f"✅ Deleted {self.name}")
    
    def get_id(self) -> Optional[str]:
        """Get the agent ID."""
        return self.agent_id
    
    def analyze_query(self, user_query: str) -> str:
        """
        Generate a prompt for the main agent to analyze which agents to use.
        
        Args:
            user_query: User's question or request
            
        Returns:
            Prompt for analysis
        """
        return f"""Analyze this user query and determine which specialized agent(s) to use:

User Query: {user_query}

Available Agents:
1. MCP Tool Agent - for weather, calculations, time, random numbers
2. RAG Research Agent - for technical questions, best practices, documentation

Respond with:
1. Which agent(s) to use and why
2. What specific question to ask each agent
3. How to synthesize the final response"""
    
    def synthesize_prompt(self, user_query: str, agent_responses: list) -> str:
        """
        Generate a prompt for synthesizing agent responses.
        
        Args:
            user_query: Original user query
            agent_responses: List of responses from specialized agents
            
        Returns:
            Synthesis prompt
        """
        import json
        
        return f"""Based on the specialized agent responses, provide a comprehensive final answer to the user.

Original Query: {user_query}

Agent Responses:
{json.dumps(agent_responses, indent=2)}

Synthesize these into a clear, well-structured final response."""

    async def run(self, message: str, thread_id: Optional[str] = None) -> str:
        """
        Run the main orchestrator agent with a message.
        
        Args:
            message: User message
            thread_id: Optional thread ID for conversation continuity
            
        Returns:
            Agent response
        """
        try:
            # ========================================================================
            # 🔍 OpenTelemetry Span for Agent Execution Tracing
            # ========================================================================
            # Wrap agent execution in a span to track each step in Tracing UI
            # ========================================================================
            from opentelemetry import trace
            tracer = trace.get_tracer(__name__)
            
            with tracer.start_as_current_span("main_agent_run") as span:
                # Gen AI semantic conventions for Azure AI Foundry Tracing
                span.set_attribute("gen_ai.system", "azure_ai_agent")
                span.set_attribute("gen_ai.request.model", self.model)
                span.set_attribute("gen_ai.prompt", message)
                span.set_attribute("agent.id", self.agent_id)
                span.set_attribute("agent.name", self.name)
                
                # Create thread (thread_id parameter not supported in current SDK)
                thread = self.project_client.agents.threads.create()
                span.set_attribute("thread.id", thread.id)
                
                # Add message to thread
                self.project_client.agents.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=message
                )
                
                # Run the agent
                run = self.project_client.agents.runs.create_and_process(
                    thread_id=thread.id,
                    agent_id=self.agent_id
                )
                span.set_attribute("run.id", run.id)
                span.set_attribute("run.status", run.status)
                
                # Get the response
                messages = self.project_client.agents.messages.list(thread_id=thread.id)
            
                # Convert ItemPaged to list for easier debugging
                messages_list = list(messages)
                logger.info(f"Retrieved {len(messages_list)} messages from thread")
                span.set_attribute("messages.count", len(messages_list))
                
                # Messages are returned in reverse chronological order (newest first)
                for msg in messages_list:
                    logger.info(f"Message role: {msg.role}, has content: {hasattr(msg, 'content')}")
                    if msg.role == "assistant":
                        # Content is a list of content parts
                        if hasattr(msg, 'content') and msg.content:
                            logger.info(f"Assistant message content parts: {len(msg.content)}")
                            for content_part in msg.content:
                                # Each content part has a 'type' and type-specific data
                                if hasattr(content_part, 'text'):
                                    response_text = content_part.text.value
                                    logger.info(f"Found response: {response_text[:100]}...")
                                    
                                    # Log output to span for Tracing UI (Gen AI conventions)
                                    span.set_attribute("gen_ai.completion", response_text)
                                    span.set_attribute("gen_ai.response.finish_reason", "stop")
                                    span.set_attribute("gen_ai.usage.output_tokens", len(response_text.split()))
                                    
                                    return response_text
                
                logger.warning("No assistant response found in messages")
                return "No response generated"
            
        except Exception as e:
            logger.error(f"Error running main agent: {e}")
            raise
