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

# OpenTelemetry imports for tracing
from opentelemetry import trace

# Import masking utility
from masking import mask_content

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
        # Priority: Parameter > Environment variable > Default fallback
        if model_deployment_name:
            self.model_deployment_name = model_deployment_name
        else:
            self.model_deployment_name = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME")
            if not self.model_deployment_name:
                logger.warning(
                    "AZURE_AI_MODEL_DEPLOYMENT_NAME not set. "
                    "Using 'gpt-4o' as fallback."
                )
                self.model_deployment_name = "gpt-4o"
        
        self.search_endpoint = search_endpoint
        self.search_index = search_index
        self.search_key = search_key
        
        self.agent: Optional[ChatAgent] = None
        self.credential: Optional[ChainedTokenCredential] = None
        self.chat_client: Optional[AzureAIAgentClient] = None
        self.search_client: Optional[SearchClient] = None
        
        self.name = "Research Agent"
        self.instructions = f"""You are a specialized research agent with access to a travel destination knowledge base via Azure AI Search.

Your knowledge base contains information about Korean travel destinations including:
- 자연/힐링: Natural healing spots, scenic mountains, valleys, and nature parks
- 문화/역사: Cultural and historical sites, traditional villages, museums
- 도시/해변: Urban destinations and beach resorts
- 액티비티/스포츠: Adventure and sports destinations (surfing, hiking, etc.)
- 먹거리/시장: Food markets and culinary destinations

Search Configuration:
- Search Index: {search_index or 'Not configured'}
- Query Type: Hybrid (Vector + Keyword)
- Top Results: 5

When answering travel-related questions:
1. First, I will search the knowledge base for relevant travel destinations
2. Then provide you with search results labeled as [Document 1], [Document 2], etc.
3. You MUST cite these documents in your answer using the format【N:0†source】where N is the document number
4. Reference specific documents when making claims or providing information
5. Provide comprehensive, well-structured travel recommendations
6. Include practical information like locations, best times to visit, activities
7. Explain why each destination matches the user's request
8. If information is not in search results, state that clearly

CITATION REQUIREMENTS:
- Always cite documents using【N:0†source】format (e.g.,【1:0†source】,【2:0†source】)
- Use this exact format with the special brackets【】
- Place citations immediately after the relevant sentence or claim
- Example: "제주도 우도는 아름다운 자연 경관을 자랑합니다【1:0†source】【2:0†source】."
- The number N corresponds to the [Document N] in the search results

IMPORTANT: Always start your response with one of these indicators:
- "📚 [RAG-based Answer]" - if your answer is based on retrieved information from the knowledge base
- "💭 [General Knowledge]" - if the information is not available in the knowledge base and you're using general knowledge

Always ground your responses in retrieved information and cite your sources (place names and categories)."""
    
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
            self.search_client = SearchClient(
                endpoint=self.search_endpoint,
                index_name=self.search_index,
                credential=AzureKeyCredential(self.search_key)
            )
            logger.info(f"Azure AI Search client initialized - Endpoint: {self.search_endpoint}, Index: {self.search_index}")
        else:
            logger.warning(f"Azure AI Search not configured (missing endpoint/index/key) - using general knowledge only")
        
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
        
        logger.info(f"{self.name} initialized - RAG: {'Enabled' if self.search_client else 'Disabled'}")
    
    async def cleanup(self):
        """Clean up resources."""
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
            
            return search_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _format_search_results(self, results: List[Dict[str, Any]]) -> str:
        """Format search results for LLM context."""
        if not results:
            return "No relevant information found in the knowledge base."
        
        formatted = "📚 Knowledge Base Search Results:\n\n"
        
        for i, result in enumerate(results, 1):
            formatted += f"[Document {i}] {result['title']}\n"
            formatted += f"Category: {result['category']}\n"
            formatted += f"Document ID: {result['id']}\n"
            formatted += f"Content: {result['content'][:500]}...\n"  # Limit content length
            formatted += f"(Relevance Score: {result['score']:.2f})\n\n"
        
        return formatted
    
    def _add_citations_to_response(self, response: str, num_sources: int) -> str:
        """
        Automatically add citations to response in Lab 3 style.
        
        Args:
            response: LLM response text
            num_sources: Number of source documents used
            
        Returns:
            Response with citations inserted
        """
        if num_sources == 0:
            return response
        
        # Split response into sentences
        import re
        sentences = re.split(r'([.!?]\s+)', response)
        
        # Add citations to key sentences (every 2-3 sentences get a citation)
        result = ""
        citation_idx = 1
        sentence_count = 0
        
        for i, part in enumerate(sentences):
            result += part
            
            # If this is a sentence ending punctuation
            if re.match(r'[.!?]\s+', part):
                sentence_count += 1
                
                # Add citation every 2-3 sentences
                if sentence_count % 2 == 0 and citation_idx <= num_sources:
                    # Insert citation before the space
                    citation = f"【{citation_idx}:0†source】"
                    result = result.rstrip() + citation + " "
                    citation_idx += 1
        
        return result.strip()
    
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
        
        # ========================================================================
        # 🔍 OpenTelemetry Span for Research Agent Execution Tracing
        # ========================================================================
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("research_agent.execute") as span:
            span.set_attribute("agent.type", "research")
            span.set_attribute("agent.message", mask_content(message))
            span.set_attribute("research.search_enabled", self.search_client is not None)
            span.set_attribute("research.index", self.search_index or "not_configured")
            
            try:
                # If search is available, perform RAG
                if self.search_client:
                    # Search knowledge base with tracing
                    with tracer.start_as_current_span("research.search") as search_span:
                        search_span.set_attribute("search.query", mask_content(message))
                        search_span.set_attribute("search.top_k", 5)
                        
                        search_results = await self._search_knowledge_base(message, top_k=5)
                        
                        search_span.set_attribute("search.results_count", len(search_results))
                        search_span.set_attribute("search.status", "success" if search_results else "no_results")
                    
                    if search_results:
                        # Format search results
                        context = self._format_search_results(search_results)
                        
                        # Create enhanced prompt with search results
                        enhanced_message = f"""{context}

User Question: {message}

Please answer based on the search results above. IMPORTANT: You MUST cite documents using【N:0†source】format where N is the document number (e.g.,【1:0†source】,【2:0†source】). Place citations immediately after claims."""
                        
                        span.set_attribute("research.mode", "rag")
                    else:
                        enhanced_message = f"""No relevant information found in knowledge base.

User Question: {message}

Please answer using your general knowledge and indicate that the information is not from the knowledge base."""
                        logger.warning("No search results found")
                        span.set_attribute("research.mode", "general_no_results")
                else:
                    # No search available - use original message
                    enhanced_message = message
                    logger.warning("Search not available - using general knowledge")
                    span.set_attribute("research.mode", "general_no_search")
                
                # Run the agent with enhanced message and tracing
                with tracer.start_as_current_span("research.generate") as gen_span:
                    gen_span.set_attribute("gen_ai.system", "azure_ai_agent_framework")
                    gen_span.set_attribute("gen_ai.request.model", self.model_deployment_name)
                    gen_span.set_attribute("gen_ai.prompt", mask_content(enhanced_message))
                    
                    result = await self.agent.run(enhanced_message, thread=thread)
                    
                    # Extract response from messages (ChatMessage has 'contents')
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
                        response_text = str(result.text if hasattr(result, 'text') else "No response")
                    
                    # Add citations automatically if RAG was used
                    if self.search_client and search_results:
                        response_text = self._add_citations_to_response(response_text, len(search_results))
                        gen_span.set_attribute("research.citations_added", len(search_results))
                    
                    gen_span.set_attribute("gen_ai.completion", mask_content(response_text))
                    gen_span.set_attribute("gen_ai.response.length", len(response_text))
                
                span.set_attribute("research.status", "success")
                span.set_attribute("research.response_length", len(response_text))
                
                return response_text
                
            except Exception as e:
                logger.error(f"Error running research agent: {e}")
                span.set_attribute("research.status", "error")
                span.set_attribute("error.message", str(e))
                span.record_exception(e)
                raise
    
    def get_new_thread(self):
        """Create a new conversation thread."""
        if not self.agent:
            raise RuntimeError("Agent not initialized")
        return self.agent.get_new_thread()
