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

# OpenTelemetry imports for tracing
from opentelemetry import trace
from azure.monitor.opentelemetry import configure_azure_monitor
from azure.ai.inference.tracing import AIInferenceInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from main_agent_workflow import MainAgentWorkflow
from masking import mask_content

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
        
        # ========================================================================
        # 🔍 Step 1: Configure Observability BEFORE creating agents
        # ========================================================================
        app_insights_conn = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        if app_insights_conn:
            logger.info("📊 Configuring Azure Monitor for observability...")
            configure_azure_monitor()
            logger.info("✅ Azure Monitor configured")
            
            # Instrument AI Inference for LLM call tracing
            AIInferenceInstrumentor().instrument()
            logger.info("✅ AI Inference instrumentation enabled")
            
            # Instrument FastAPI for HTTP request tracing
            FastAPIInstrumentor.instrument_app(app)
            logger.info("✅ FastAPI instrumentation enabled")
        else:
            logger.warning("⚠️  APPLICATIONINSIGHTS_CONNECTION_STRING not set - Observability disabled")
        
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
        logger.info(f"   Tool Agent (MCP): {'Enabled (Weather via wttr.in API)' if mcp_endpoint else 'Disabled (MCP_ENDPOINT not set)'}")
        logger.info(f"   Research Agent (RAG): {'Enabled (Korean Travel Destinations)' if search_index else 'Disabled (SEARCH_INDEX not set)'}")
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
    
    # ========================================================================
    # 🔍 OpenTelemetry Span for HTTP Request Tracing
    # ========================================================================
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("api.chat") as span:
        span.set_attribute("http.method", "POST")
        span.set_attribute("http.route", "/chat")
        span.set_attribute("http.request.message", mask_content(request.message))
        
        try:
            logger.info(f"📨 Main Agent Workflow request: {request.message[:100]}...")
            
            response_text = await main_agent.run(request.message)
            
            span.set_attribute("http.status_code", 200)
            span.set_attribute("http.response.length", len(response_text))
            span.set_attribute("api.status", "success")
            
            return AgentResponse(response=response_text)
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            span.set_attribute("http.status_code", 500)
            span.set_attribute("api.status", "error")
            span.set_attribute("error.message", str(e))
            span.record_exception(e)
            raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
