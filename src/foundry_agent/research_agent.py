"""
Research Agent - Searches knowledge base using Azure AI Search with RAG
"""

import logging
import os
from typing import Optional

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ConnectionType
from azure.ai.agents.models import AzureAISearchTool

logger = logging.getLogger(__name__)


class ResearchAgent:
    """
    Specialized research agent with access to a knowledge base via Azure AI Search.
    Uses RAG (Retrieval-Augmented Generation) pattern.
    """
    
    def __init__(
        self,
        project_client: AIProjectClient,
        search_endpoint: str,
        search_key: str,
        search_index: str
    ):
        """
        Initialize the Research Agent.
        
        Args:
            project_client: AIProjectClient instance
            search_endpoint: Azure AI Search endpoint (not used with AzureAISearchTool)
            search_key: Azure AI Search admin key (not used with AzureAISearchTool)
            search_index: Name of the search index
        """
        self.project_client = project_client
        self.search_index = search_index
        self.search_endpoint = search_endpoint
        self.search_key = search_key
        self.agent_id: Optional[str] = None
        
        # Try to get Azure AI Search connection from project (preferred)
        connection_id = None
        try:
            search_connection = project_client.connections.get_default(ConnectionType.AZURE_AI_SEARCH)
            connection_id = search_connection.id
            logger.info(f"Found Azure AI Search connection: {connection_id}")
        except Exception as e:
            logger.warning(f"Could not get default Azure AI Search connection: {e}")
            # Fallback: try to find any Azure AI Search connection
            try:
                connections = list(project_client.connections.list(connection_type=ConnectionType.AZURE_AI_SEARCH))
                if connections:
                    connection_id = connections[0].id
                    logger.info(f"Using first available Azure AI Search connection: {connection_id}")
            except Exception as e2:
                logger.warning(f"Could not list Azure AI Search connections: {e2}")
        
        # If no connection found, we'll use direct endpoint/key (via environment variables in container)
        if connection_id:
            # Use connection-based approach
            self.ai_search_tool = AzureAISearchTool(
                index_connection_id=connection_id,
                index_name=search_index,
                top_k=5
            )
            logger.info(f"Initialized AzureAISearchTool with connection ID: {connection_id}")
        else:
            # Use direct endpoint/key approach
            # Note: AzureAISearchTool still requires a connection, so we'll need to create one
            logger.warning("No Azure AI Search connection found - Research Agent will have limited functionality")
            logger.info(f"Search endpoint: {search_endpoint}, Index: {search_index}")
            # For now, set ai_search_tool to None - agent will be created without it
            self.ai_search_tool = None
        
        self.name = "Research Agent"
        # Get model deployment name from environment variable (default: gpt-5)
        self.model = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-5")
        self.instructions = f"""You are a specialized research agent with access to a knowledge base via Azure AI Search.

Your knowledge base contains information about:
- AI Agent development patterns and best practices
- RAG (Retrieval-Augmented Generation) implementation
- Model Context Protocol (MCP)
- Azure AI Foundry Agent Service
- Deployment strategies and architecture patterns
- Multi-agent orchestration
- Connected Agents patterns

Search Configuration:
- Search Index: {search_index}
- Query Type: Hybrid (Vector + Keyword)
- Top Results: 5

When answering questions:
1. Use the Azure AI Search tool to find relevant information in your knowledge base
2. Cite specific sources from the search results
3. Provide comprehensive, well-structured answers
4. Include code examples when available
5. Explain concepts clearly with context
6. If information is not in the knowledge base, clearly state that

Always ground your responses in retrieved information and cite your sources."""
    
    def create(self) -> str:
        """Create the agent in Azure AI Foundry."""
        logger.info(f"Creating agent: {self.name}")
        
        # Create agent with or without Azure AI Search tool
        if self.ai_search_tool:
            agent = self.project_client.agents.create_agent(
                model=self.model,
                name=self.name,
                instructions=self.instructions,
                tools=self.ai_search_tool.definitions,
                tool_resources=self.ai_search_tool.resources
            )
            logger.info(f"✅ Created {self.name} with Azure AI Search tool")
        else:
            # Create agent without tools - will use general knowledge only
            logger.warning(f"Creating {self.name} without Azure AI Search tool")
            agent = self.project_client.agents.create_agent(
                model=self.model,
                name=self.name,
                instructions=self.instructions + "\n\nNote: Azure AI Search is not available. Use your general knowledge to answer questions."
            )
            logger.info(f"✅ Created {self.name} (no tools)")
        
        self.agent_id = agent.id
        logger.info(f"Agent ID: {self.agent_id}")
        return self.agent_id
    
    def delete(self):
        """Delete the agent."""
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
            name="research_agent",
            description="""Use this agent for:
- Technical questions about AI, machine learning, and software development
- Best practices and architectural patterns
- Documentation searches and knowledge base queries
- RAG (Retrieval-Augmented Generation) implementation questions
- Azure AI Foundry and Agent Service questions
- Model Context Protocol (MCP) documentation
- Multi-agent orchestration patterns

This agent has access to a comprehensive knowledge base via Azure AI Search."""
        )
    
    def get_id(self) -> Optional[str]:
        """Get the agent ID."""
        return self.agent_id
    
    async def run(self, message: str, thread_id: Optional[str] = None) -> str:
        """
        Run the research agent with a message.
        
        Args:
            message: User message
            thread_id: Optional thread ID for conversation continuity
            
        Returns:
            Agent response
        """
        try:
            # ========================================================================
            # 🔍 OpenTelemetry Span for Research Agent Execution Tracing
            # ========================================================================
            from opentelemetry import trace
            tracer = trace.get_tracer(__name__)
            
            with tracer.start_as_current_span("research_agent_run") as span:
                # Gen AI semantic conventions
                span.set_attribute("gen_ai.system", "azure_ai_agent")
                span.set_attribute("gen_ai.request.model", self.model)
                span.set_attribute("gen_ai.prompt", message)
                span.set_attribute("agent.id", self.agent_id)
                span.set_attribute("agent.name", self.name)
                span.set_attribute("agent.type", "research_agent")
                
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
                                    
                                    # Log output to span for Tracing UI
                                    span.set_attribute("gen_ai.completion", response_text)
                                    span.set_attribute("gen_ai.response.finish_reason", "stop")
                                    span.set_attribute("gen_ai.usage.output_tokens", len(response_text.split()))
                                    
                                    return response_text
                
                logger.warning("No assistant response found in messages")
                return "No response generated"
            
        except Exception as e:
            logger.error(f"Error running research agent: {e}")
            raise
