"""
Research Agent - Microsoft Agent Framework Implementation
Searches knowledge base using Azure AI Search with RAG
"""

import asyncio
import logging
import os
from typing import Optional, List, Dict, Any

from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import AzureCliCredential, ManagedIdentityCredential, ChainedTokenCredential
from azure.search.documents.aio import SearchClient
from azure.core.credentials import AzureKeyCredential

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
        search_index: Optional[str] = None,
        search_key: Optional[str] = None
    ):
        """
        Initialize the Research Agent.
        
        Args:
            project_endpoint: Azure AI Project endpoint
            model_deployment_name: Model deployment name
            search_endpoint: Azure AI Search endpoint
            search_index: Name of the search index
            search_key: Azure AI Search admin key
        """
        self.project_endpoint = project_endpoint
        self.model_deployment_name = model_deployment_name or "gpt-4o"
        self.search_endpoint = search_endpoint
        self.search_index = search_index
        self.search_key = search_key
        
        self.agent: Optional[ChatAgent] = None
        self.credential: Optional[ChainedTokenCredential] = None
        self.chat_client: Optional[AzureAIAgentClient] = None
        self.search_client: Optional[SearchClient] = None
        
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
1. First, I will search the knowledge base for relevant information
2. Then provide you with search results
3. You should cite specific sources from search results
4. Provide comprehensive, well-structured answers
5. Include code examples when available
6. Explain concepts clearly with context
7. If information is not in search results, state that clearly

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
        
        # Initialize Azure AI Search client if endpoint and key are provided
        if self.search_endpoint and self.search_index and self.search_key:
            logger.info(f"Initializing Azure AI Search client...")
            logger.info(f"   Endpoint: {self.search_endpoint}")
            logger.info(f"   Index: {self.search_index}")
            
            self.search_client = SearchClient(
                endpoint=self.search_endpoint,
                index_name=self.search_index,
                credential=AzureKeyCredential(self.search_key)
            )
            logger.info(f"✅ Azure AI Search client initialized")
        else:
            logger.warning(f"⚠️  Azure AI Search not configured (missing endpoint/index/key)")
            logger.warning(f"   Research Agent will use general knowledge only")
        
        # Create Azure AI Agent Client
        self.chat_client = AzureAIAgentClient(
            project_endpoint=self.project_endpoint,
            model_deployment_name=self.model_deployment_name,
            async_credential=self.credential,
        )
        
        # Create the agent
        self.agent = self.chat_client.create_agent(
            name=self.name,
            instructions=self.instructions
        )
        
        logger.info(f"✅ Initialized {self.name}")
        if self.search_client:
            logger.info(f"   RAG: Enabled with Azure AI Search")
        else:
            logger.info(f"   RAG: Disabled (general knowledge only)")
    
    async def cleanup(self):
        """Clean up resources."""
        logger.info(f"Cleaning up {self.name}")
        
        if self.agent:
            self.agent = None
        
        if self.search_client:
            await self.search_client.close()
            self.search_client = None
        
        if self.chat_client:
            await self.chat_client.close()
            self.chat_client = None
        
        if self.credential:
            await self.credential.close()
            self.credential = None
        
        # Give time for connections to close properly
        await asyncio.sleep(0.1)
        
        logger.info(f"✅ Cleaned up {self.name}")
    
    async def _search_knowledge_base(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the knowledge base using Azure AI Search.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of search results with content and metadata
        """
        if not self.search_client:
            logger.warning("Search client not initialized - returning empty results")
            return []
        
        try:
            logger.info(f"🔍 Searching knowledge base: '{query}' (top {top_k})")
            
            # Perform hybrid search (vector + keyword)
            results = await self.search_client.search(
                search_text=query,
                top=top_k,
                select=["id", "title", "content", "category"]
            )
            
            # Collect results
            search_results = []
            async for result in results:
                search_results.append({
                    "id": result.get("id", "unknown"),
                    "title": result.get("title", "Untitled"),
                    "content": result.get("content", ""),
                    "category": result.get("category", "general"),
                    "score": result.get("@search.score", 0.0)
                })
            
            logger.info(f"✅ Found {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    def _format_search_results(self, results: List[Dict[str, Any]]) -> str:
        """Format search results for LLM context."""
        if not results:
            return "No relevant information found in the knowledge base."
        
        formatted = "📚 Knowledge Base Search Results:\n\n"
        
        for i, result in enumerate(results, 1):
            formatted += f"[Result {i}] {result['title']}\n"
            formatted += f"Category: {result['category']}\n"
            formatted += f"Content: {result['content'][:500]}...\n"  # Limit content length
            formatted += f"(Relevance: {result['score']:.2f})\n\n"
        
        return formatted
    
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
            
            # If search is available, perform RAG
            if self.search_client:
                # Search knowledge base
                search_results = await self._search_knowledge_base(message, top_k=5)
                
                if search_results:
                    # Format search results
                    context = self._format_search_results(search_results)
                    
                    # Create enhanced prompt with search results
                    enhanced_message = f"""{context}

User Question: {message}

Please answer based on the search results above. Cite sources by their [Result N] number."""
                    
                    logger.info(f"🔍 Enhanced prompt with {len(search_results)} search results")
                else:
                    enhanced_message = f"""No relevant information found in knowledge base.

User Question: {message}

Please answer using your general knowledge and indicate that the information is not from the knowledge base."""
                    logger.warning("⚠️  No search results found")
            else:
                # No search available - use original message
                enhanced_message = message
                logger.warning("⚠️  Search not available - using general knowledge")
            
            # Run the agent with enhanced message
            result = await self.agent.run(enhanced_message, thread=thread)
            
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
