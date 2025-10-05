"""
API Server for Main Agent - HTTP interface for agent interactions
"""

import os
import time
import logging
from typing import Optional
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential, ChainedTokenCredential

from main_agent import MainAgent
from tool_agent import ToolAgent
from research_agent import ResearchAgent

# Load environment variables
import pathlib
env_path = pathlib.Path("/app/.env")
if env_path.exists():
    print(f"✅ Loading .env from: {env_path}")
    load_dotenv(dotenv_path=env_path)
else:
    print("⚠️  /app/.env not found, loading from current directory")
    load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Verify critical environment variables
required_vars = ["PROJECT_CONNECTION_STRING", "MCP_ENDPOINT", "SEARCH_ENDPOINT", "SEARCH_KEY", "SEARCH_INDEX"]
print("\n📋 Environment Variables Check:")
for var in required_vars:
    value = os.getenv(var)
    if value:
        # Mask sensitive values
        if "KEY" in var or "STRING" in var:
            masked = value[:20] + "..." if len(value) > 20 else "***"
            print(f"  ✅ {var}: {masked}")
        else:
            print(f"  ✅ {var}: {value}")
    else:
        print(f"  ❌ {var}: NOT SET")
print()

# Initialize FastAPI app
app = FastAPI(title="Main Agent API", version="1.0.0")

# Global variables
project_client: Optional[AIProjectClient] = None
main_agent: Optional[MainAgent] = None
tool_agent: Optional[ToolAgent] = None
research_agent: Optional[ResearchAgent] = None

# Request/Response models
class AgentRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

class AgentResponse(BaseModel):
    response: str
    thread_id: str

@app.on_event("startup")
async def startup_event():
    """Initialize agents on startup"""
    global project_client, main_agent, tool_agent, research_agent
    
    try:
        logger.info("🚀 Initializing Agent Service...")
        
        # Get connection string
        conn_str = os.getenv("PROJECT_CONNECTION_STRING")
        if not conn_str:
            raise ValueError("PROJECT_CONNECTION_STRING environment variable not set")
        
        # Parse project endpoint
        parts = conn_str.split(';')
        project_endpoint = parts[0]
        
        # Initialize Azure AI Project Client with ChainedTokenCredential
        credential = ChainedTokenCredential(
            ManagedIdentityCredential(),
            DefaultAzureCredential()
        )
        
        project_client = AIProjectClient(
            credential=credential,
            endpoint=project_endpoint
        )
        logger.info("✅ Azure AI Project Client initialized")
        
        # Create sub-agents
        mcp_endpoint = os.getenv("MCP_ENDPOINT")
        
        # 1. Tool Agent (MCP)
        logger.info(f"Creating Tool Agent (MCP: {mcp_endpoint})...")
        tool_agent = ToolAgent(project_client=project_client, mcp_server_url=mcp_endpoint)
        tool_agent_id = await tool_agent.create()
        logger.info(f"✅ Tool Agent created: {tool_agent_id}")
        
        # 2. Research Agent (RAG)
        search_endpoint = os.getenv("SEARCH_ENDPOINT")
        search_key = os.getenv("SEARCH_KEY")
        search_index = os.getenv("SEARCH_INDEX")
        
        logger.info(f"Creating Research Agent (Index: {search_index})...")
        research_agent = ResearchAgent(
            project_client=project_client,
            search_endpoint=search_endpoint,
            search_key=search_key,
            search_index=search_index
        )
        research_agent_id = research_agent.create()
        logger.info(f"✅ Research Agent created: {research_agent_id}")
        
        # 3. Get connected tools from sub-agents
        connected_tools = []
        
        # Add Tool Agent's connected tool
        if hasattr(tool_agent, 'get_connected_tool'):
            connected_tools.append(tool_agent.get_connected_tool())
        
        # Add Research Agent's connected tool
        if hasattr(research_agent, 'get_connected_tool'):
            connected_tools.append(research_agent.get_connected_tool())
        
        # 4. Main Agent with connected agents
        logger.info("Creating Main Agent with connected agents...")
        main_agent = MainAgent(
            project_client=project_client,
            connected_tools=connected_tools
        )
        agent_id = main_agent.create()
        logger.info(f"✅ Main Agent ready: {agent_id}")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        raise

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Agent API Server",
        "agents": {
            "main_agent": main_agent is not None,
            "tool_agent": tool_agent is not None,
            "research_agent": research_agent is not None
        }
    }

@app.post("/chat", response_model=AgentResponse)
async def chat_with_main_agent(request: AgentRequest):
    """Chat with the main agent"""
    if not main_agent:
        raise HTTPException(status_code=503, detail="Main agent not initialized")
    
    try:
        logger.info(f"💬 Main Agent request: {request.message[:100]}...")
        
        response_text = await main_agent.run(
            message=request.message,
            thread_id=request.thread_id
        )
        
        # thread_id는 현재 구현에서 반환하지 않으므로 임시로 "main-thread" 사용
        return AgentResponse(response=response_text, thread_id="main-thread")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tool-agent/chat", response_model=AgentResponse)
async def chat_with_tool_agent(request: AgentRequest):
    """Chat with the tool agent directly"""
    if not tool_agent:
        raise HTTPException(status_code=503, detail="Tool agent not initialized")
    
    try:
        logger.info(f"🔧 Tool Agent request: {request.message[:100]}...")
        
        response_text = await tool_agent.run(
            message=request.message,
            thread_id=request.thread_id
        )
        
        # thread_id는 현재 구현에서 반환하지 않으므로 임시로 "tool-thread" 사용
        return AgentResponse(response=response_text, thread_id="tool-thread")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/research-agent/chat", response_model=AgentResponse)
async def chat_with_research_agent(request: AgentRequest):
    """Chat with the research agent directly"""
    if not research_agent:
        raise HTTPException(status_code=503, detail="Research agent not initialized")
    
    try:
        logger.info(f"📚 Research Agent request: {request.message[:100]}...")
        
        response_text = await research_agent.run(
            message=request.message,
            thread_id=request.thread_id
        )
        
        # thread_id는 현재 구현에서 반환하지 않으므로 임시로 "research-thread" 사용
        return AgentResponse(response=response_text, thread_id="research-thread")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
