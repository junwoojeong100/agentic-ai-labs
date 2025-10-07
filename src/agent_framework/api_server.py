"""
API Server for Multi-Agent System - Microsoft Agent Framework Implementation
HTTP interface for agent interactions using Workflow Pattern
"""

import os
import logging
import asyncio
from typing import Optional
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from main_agent_workflow import MainAgentWorkflow

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Verify environment variables
required_vars = ["AZURE_AI_PROJECT_ENDPOINT"]
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
app = FastAPI(title="Agent Framework API", version="1.0.0")

# Global variables
main_agent: Optional[MainAgentWorkflow] = None

# Request/Response models
class AgentRequest(BaseModel):
    message: str

class AgentResponse(BaseModel):
    response: str


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup agents on shutdown"""
    global main_agent
    
    logger.info("🛑 Shutting down agents...")
    
    # Cleanup all agent instances
    try:
        from main_agent_workflow import cleanup_all_agents
        await cleanup_all_agents()
        logger.info("✅ All agents cleaned up")
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")
    
    main_agent = None
    
    logger.info("✅ Shutdown complete")


@app.on_event("startup")
async def startup_event():
    """Initialize agents on startup"""
    global main_agent
    
    try:
        logger.info("🚀 Initializing Agent Framework Service...")
        
        # Get configuration
        project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
        if not project_endpoint:
            raise ValueError("AZURE_AI_PROJECT_ENDPOINT not set")
        
        mcp_endpoint = os.getenv("MCP_ENDPOINT")
        search_endpoint = os.getenv("SEARCH_ENDPOINT")
        search_index = os.getenv("SEARCH_INDEX")
        
        # Create main agent with workflow orchestration
        logger.info("Creating Main Agent Workflow with orchestration...")
        main_agent = MainAgentWorkflow()
        
        logger.info("✅ Main Agent Workflow initialized")
        logger.info(f"   Tool Agent (MCP): {'Enabled' if mcp_endpoint else 'Disabled (MCP_ENDPOINT not set)'}")
        logger.info(f"   Research Agent (RAG): {'Enabled' if search_index else 'Disabled (SEARCH_INDEX not set)'}")
        logger.info(f"   Orchestrator: Enabled (for complex queries)")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        raise


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "status": "running",
        "service": "Agent Framework API Server",
        "framework": "Microsoft Agent Framework - Workflow Pattern",
        "agents": {
            "main_agent_workflow": main_agent is not None,
            "orchestrator": True,
            "tool_routing": True,
            "research_routing": True,
            "general_routing": True
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Agent Framework API Server"
    }


@app.post("/chat", response_model=AgentResponse)
async def chat_with_main_agent(request: AgentRequest):
    """Chat with the main agent workflow (supports all routing: tool, research, orchestrator, general)"""
    if not main_agent:
        raise HTTPException(status_code=503, detail="Main agent not initialized")
    
    try:
        logger.info(f"� Main Agent Workflow request: {request.message[:100]}...")
        
        response_text = await main_agent.run(request.message)
        
        return AgentResponse(response=response_text)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
