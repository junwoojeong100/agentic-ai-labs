"""
Research Agent - Microsoft Agent Framework Implementation
Searches knowledge base using Azure AI Search with RAG
"""

import asyncio
import logging
import os
from typing import Optional

from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import AzureCliCredential, ManagedIdentityCredential, ChainedTokenCredential

logger = logging.getLogger(__name__)


class ResearchAgent:
    """
    Specialized research agent with RAG (Retrieval-Augmented Generation).
    Uses Microsoft Agent Framework with Azure AI Search integration.
    """
    
    def __init__(
        self,
        project_endpoint: Optional[str] = None,
        model_deployment_name: Optional[str] = None,
        search_endpoint: Optional[str] = None,
        search_index: Optional[str] = None
    ):
        """
        Initialize the Research Agent.
        
        Args:
            project_endpoint: Azure AI Project endpoint
            model_deployment_name: Model deployment name
            search_endpoint: Azure AI Search endpoint
            search_index: Name of the search index
        """
        self.project_endpoint = project_endpoint
        self.model_deployment_name = model_deployment_name or "gpt-4o"
        self.search_endpoint = search_endpoint
        self.search_index = search_index
        
        self.agent: Optional[ChatAgent] = None
        self.credential: Optional[ChainedTokenCredential] = None
        self.chat_client: Optional[AzureAIAgentClient] = None
        
        self.name = "Research Agent"
        self.instructions = f"""You are a specialized research agent with access to a knowledge base.

Your knowledge base contains information about:
- AI Agent development patterns and best practices
- RAG (Retrieval-Augmented Generation) implementation
- Model Context Protocol (MCP)
- Azure AI Foundry Agent Service
- Deployment strategies and architecture patterns
- Multi-agent orchestration
- Connected Agents patterns

Search Configuration:
- Search Index: {search_index or 'Not configured'}
- Query Type: Hybrid (Vector + Keyword)
- Top Results: 5

When answering questions:
1. Search the knowledge base for relevant information
2. Cite specific sources from search results
3. Provide comprehensive, well-structured answers
4. Include code examples when available
5. Explain concepts clearly with context
6. If information is not in knowledge base, state that clearly

IMPORTANT: Always start your response with one of these indicators:
- "📚 [RAG-based Answer]" - if your answer is based on retrieved information from the knowledge base
- "💭 [General Knowledge]" - if the information is not available in the knowledge base and you're using general knowledge

Always ground your responses in retrieved information and cite sources when using RAG."""
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
    
    async def initialize(self):
        """Initialize the agent."""
        logger.info(f"Initializing {self.name}")
        
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
        
        # Note: Azure AI Search integration in Agent Framework requires
        # the search to be configured at the project level or via tools
        # For now, we create a basic agent without direct search integration
        # In production, you would add AzureAISearchTool or similar
        
        self.agent = self.chat_client.create_agent(
            name=self.name,
            instructions=self.instructions
        )
        
        logger.info(f"✅ Initialized {self.name}")
        logger.info(f"ℹ️  Note: Direct Azure AI Search integration requires project-level configuration")
    
    async def cleanup(self):
        """Clean up resources."""
        logger.info(f"Cleaning up {self.name}")
        
        if self.agent:
            self.agent = None
        
        if self.chat_client:
            await self.chat_client.close()
            self.chat_client = None
        
        if self.credential:
            await self.credential.close()
            self.credential = None
        
        # Give time for connections to close properly
        await asyncio.sleep(0.1)
        
        logger.info(f"✅ Cleaned up {self.name}")
    
    async def run(self, message: str, thread=None) -> str:
        """
        Run the research agent with a message.
        
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
            
            # Run the agent
            result = await self.agent.run(message, thread=thread)
            
            # Extract text from result
            response_text = result.text if hasattr(result, 'text') else str(result)
            
            logger.info(f"✅ {self.name} response: {response_text[:100]}...")
            return response_text
            
        except Exception as e:
            logger.error(f"Error running research agent: {e}")
            raise
    
    def get_new_thread(self):
        """Create a new conversation thread."""
        if not self.agent:
            raise RuntimeError("Agent not initialized")
        return self.agent.get_new_thread()
