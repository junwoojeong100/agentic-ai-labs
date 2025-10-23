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
            logger.warning(f"No default Azure AI Search connection: {e}")
            # Fallback: try to find any Azure AI Search connection
            try:
                connections = list(project_client.connections.list(connection_type=ConnectionType.AZURE_AI_SEARCH))
                if connections:
                    connection_id = connections[0].id
                    logger.info(f"Using first available connection: {connection_id}")
            except Exception:
                pass
        
        # Configure AzureAISearchTool
        if connection_id:
            self.ai_search_tool = AzureAISearchTool(
                index_connection_id=connection_id,
                index_name=search_index,
                top_k=5
            )
            logger.info(f"AzureAISearchTool configured: {connection_id}")
        else:
            logger.warning("No Azure AI Search connection - Research Agent will have limited functionality")
            self.ai_search_tool = None
        
        self.name = "Research Agent"
        self.model = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-5")
        self.instructions = f"""You are a specialized research agent with access to a travel destination knowledge base via Azure AI Search.

Your knowledge base contains information about Korean travel destinations including:
- 자연/힐링: Natural healing spots, scenic mountains, valleys, and nature parks
- 문화/역사: Cultural and historical sites, traditional villages, museums
- 도시/해변: Urban destinations and beach resorts
- 액티비티/스포츠: Adventure and sports destinations (surfing, hiking, etc.)
- 먹거리/시장: Food markets and culinary destinations

Search Configuration:
- Search Index: {search_index}
- Query Type: Hybrid (Vector + Keyword)
- Top Results: 5

When answering travel-related questions:
1. Use the Azure AI Search tool to find relevant travel destinations in your knowledge base
2. Cite specific sources from the search results (mention place names)
3. Provide comprehensive, well-structured travel recommendations
4. Include practical information like locations, best times to visit, activities
5. Explain why each destination matches the user's request
6. If information is not in the knowledge base, clearly state that

Always ground your responses in retrieved information and cite your sources (place names and categories)."""
    
    def create(self) -> str:
        """Create the agent in Azure AI Foundry."""
        logger.info(f"Creating {self.name}")
        
        # Create agent with or without Azure AI Search tool
        if self.ai_search_tool:
            agent = self.project_client.agents.create_agent(
                model=self.model,
                name=self.name,
                instructions=self.instructions,
                tools=self.ai_search_tool.definitions,
                tool_resources=self.ai_search_tool.resources
            )
            logger.info(f"Created {self.name} with Azure AI Search tool")
        else:
            # Create agent without tools - will use general knowledge only
            logger.warning(f"Creating {self.name} without Azure AI Search tool")
            agent = self.project_client.agents.create_agent(
                model=self.model,
                name=self.name,
                instructions=self.instructions + "\n\nNote: Azure AI Search is not available. Use your general knowledge to answer questions."
            )
            logger.info(f"Created {self.name} (no tools)")
        
        self.agent_id = agent.id
        return self.agent_id
    
    def delete(self):
        """Delete the agent."""
        if self.agent_id:
            self.project_client.agents.delete_agent(self.agent_id)
            self.agent_id = None
    
    def get_connected_tool(self):
        """Return this agent as a ConnectedAgentTool for use in Main Agent."""
        from azure.ai.agents.models import ConnectedAgentTool
        
        if not self.agent_id:
            raise ValueError("Agent must be created before getting connected tool")
        
        return ConnectedAgentTool(
            id=self.agent_id,
            name="research_agent",
            description="""Use this agent for:
- Travel destination recommendations and tourism information
- Searching for places to visit in Korea (제주도, 부산, 강원도, etc.)
- Information about natural healing spots, beaches, mountains, cultural sites
- Activity-based recommendations (힐링, 서핑, 등산, 문화 체험, etc.)
- Family-friendly destinations and tourism planning
- Food markets and culinary destinations

This agent has access to a comprehensive Korean travel destination knowledge base via Azure AI Search.
Use this agent whenever users ask about 여행지, 관광지, 추천, 명소, or specific place names."""
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
        thread = None
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
                
                # Create thread
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
                
                messages_list = list(messages)
                span.set_attribute("messages.count", len(messages_list))
                
                # Messages are returned in reverse chronological order (newest first)
                for msg in messages_list:
                    if msg.role == "assistant":
                        if hasattr(msg, 'content') and msg.content:
                            for content_part in msg.content:
                                if hasattr(content_part, 'text'):
                                    response_text = content_part.text.value
                                    
                                    # Log output to span for Tracing UI
                                    span.set_attribute("gen_ai.completion", response_text)
                                    span.set_attribute("gen_ai.response.finish_reason", "stop")
                                    span.set_attribute("gen_ai.usage.output_tokens", len(response_text.split()))
                                    
                                    return response_text
                
                logger.warning("No assistant response found")
                return "No response generated"
            
        except Exception as e:
            logger.error(f"Error: {e}")
            raise
        finally:
            # Clean up thread
            if thread:
                try:
                    self.project_client.agents.threads.delete(thread.id)
                except Exception as cleanup_error:
                    logger.warning(f"Thread cleanup failed: {cleanup_error}")
