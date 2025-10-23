"""
API Server for Main Agent - HTTP interface for agent interactions
"""

import os
import time
import logging
import asyncio
from typing import Optional
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential, ChainedTokenCredential

from main_agent import MainAgent
from tool_agent import ToolAgent
from research_agent import ResearchAgent
from masking import mask_text, get_mode

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
credential: Optional[ChainedTokenCredential] = None
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

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup agents on shutdown"""
    global main_agent, tool_agent, research_agent, project_client, credential
    
    logger.info("🛑 Shutting down agents...")
    
    # Delete Main Agent
    if main_agent:
        try:
            main_agent.delete()
            logger.info("✅ Main Agent deleted")
        except Exception as e:
            logger.error(f"❌ Error deleting Main Agent: {e}")
        finally:
            main_agent = None
    
    # Delete Tool Agent (with MCP cleanup)
    if tool_agent:
        try:
            await tool_agent.delete()
            logger.info("✅ Tool Agent deleted")
        except Exception as e:
            logger.error(f"❌ Error deleting Tool Agent: {e}")
        finally:
            tool_agent = None
    
    # Delete Research Agent
    if research_agent:
        try:
            research_agent.delete()
            logger.info("✅ Research Agent deleted")
        except Exception as e:
            logger.error(f"❌ Error deleting Research Agent: {e}")
        finally:
            research_agent = None
    
    # Close AIProjectClient to release connection resources
    if project_client:
        try:
            # AIProjectClient may have a close() method depending on SDK version
            if hasattr(project_client, 'close'):
                if asyncio.iscoroutinefunction(project_client.close):
                    await project_client.close()
                else:
                    project_client.close()
                logger.info("✅ Project client closed")
            else:
                # If no close method, just clear reference
                logger.info("🧹 Clearing project client reference...")
            project_client = None
        except Exception as e:
            logger.error(f"❌ Error closing project client: {e}")
    
    # Close credential to release token cache and resources
    if credential:
        try:
            if hasattr(credential, 'close'):
                if asyncio.iscoroutinefunction(credential.close):
                    await credential.close()
                else:
                    credential.close()
                logger.info("✅ Credential closed")
            else:
                logger.info("🧹 Clearing credential reference...")
            credential = None
        except Exception as e:
            logger.error(f"❌ Error closing credential: {e}")
    
    logger.info("✅ All agents and resources cleaned up")


@app.on_event("startup")
async def startup_event():
    """Initialize agents on startup"""
    global project_client, credential, main_agent, tool_agent, research_agent
    
    try:
        logger.info("🚀 Initializing Agent Service...")
        
        # Get connection string
        conn_str = os.getenv("PROJECT_CONNECTION_STRING")
        if not conn_str:
            raise ValueError("PROJECT_CONNECTION_STRING environment variable not set")
        
        # Parse project endpoint
        parts = conn_str.split(';')
        project_endpoint = parts[0]
        
        # ========================================================================
        # ⚡ CRITICAL: Tracing configuration for Azure AI Foundry
        # ========================================================================
        # Azure AI Foundry Tracing requires:
        # 1. Application Insights instrumentation (configure_azure_monitor)
        # 2. Content recording enabled in AIProjectClient
        # ========================================================================
        
        # Get Application Insights connection string early
        app_insights_conn_str = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        content_recording_flag = os.getenv("AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED", "false").lower() in ["1", "true", "yes"]
        
        # Configure OpenTelemetry BEFORE creating AIProjectClient
        if app_insights_conn_str:
            from azure.monitor.opentelemetry import configure_azure_monitor
            
            # ========================================================================
            # 🔥 CRITICAL: Configure OpenTelemetry with FULL instrumentation
            # ========================================================================
            # This MUST be called before any Azure SDK operations
            # resource_attributes help identify traces in Application Insights
            # ========================================================================
            configure_azure_monitor(
                connection_string=app_insights_conn_str,
                enable_live_metrics=True,
                logger_name="azure",
                instrumentation_options={
                    "azure_sdk": {"enabled": True},
                    "django": {"enabled": False},
                    "fastapi": {"enabled": True},
                    "flask": {"enabled": False},
                    "psycopg2": {"enabled": False},
                    "requests": {"enabled": True},
                    "urllib": {"enabled": True},
                    "urllib3": {"enabled": True},
                }
            )
            logger.info("✅ Azure Monitor OpenTelemetry configured with full instrumentation")
            # Log content recording status (helps operators verify prompt/completion capture)
            if content_recording_flag:
                logger.info("✅ GenAI content recording ENABLED (prompts & completions will be sent to telemetry)")
            else:
                logger.warning("⚠️  GenAI content recording DISABLED (set AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true to capture Input/Output)")
            logger.info(f"🔐 Masking mode: {get_mode()} (env AGENT_MASKING_MODE)")

            # ================================================================
            # 📡 AIAgentsInstrumentor (standard agent/tool span auto-instrumentation)
            # ================================================================
            try:
                from azure.ai.agents.telemetry import AIAgentsInstrumentor  # type: ignore
                AIAgentsInstrumentor().instrument()
                logger.info("✅ AIAgentsInstrumentor enabled (standard agent/tool spans will be emitted)")
            except ImportError:
                logger.warning("⚠️  AIAgentsInstrumentor not available (upgrade azure-ai-projects if needed)")
            except Exception as ag_err:
                logger.warning(f"⚠️  Failed to enable AIAgentsInstrumentor: {ag_err}")
        
        # Initialize Azure AI Project Client with tracing enabled
        credential = ChainedTokenCredential(
            ManagedIdentityCredential(),
            DefaultAzureCredential()
        )
        
        project_client = AIProjectClient(
            credential=credential,
            endpoint=project_endpoint,
            # Enable content recording for Tracing UI Input/Output
            user_agent="agentic-ai-labs/1.0",
            logging_enable=True
        )
        logger.info("✅ Azure AI Project Client initialized")

        # Defensive: if env var true but user accidentally removed semantic attributes later, give hint
        if content_recording_flag:
            logger.info("ℹ️  Expecting span attributes gen_ai.prompt / gen_ai.completion to appear in traces.")
        
        # ========================================================================
        # 🔍 Azure AI Inference Tracing Configuration
        # ========================================================================
        # Enable detailed tracing for Azure AI Inference calls
        # ========================================================================
        if app_insights_conn_str:
            try:
                from azure.ai.inference.tracing import AIInferenceInstrumentor  # type: ignore
                AIInferenceInstrumentor().instrument()
                logger.info("✅ Azure AI Inference Tracing enabled")
            except ImportError:
                logger.warning("⚠️  azure-ai-inference not installed, skipping AIInferenceInstrumentor")
            except Exception as trace_error:
                logger.warning(f"⚠️  Failed to enable AI Inference Tracing: {trace_error}")
            
            # Also instrument HTTP requests
            try:
                from opentelemetry.instrumentation.requests import RequestsInstrumentor
                RequestsInstrumentor().instrument()
                try:
                    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor  # type: ignore
                    HTTPXClientInstrumentor().instrument()
                except Exception:
                    logger.warning("⚠️  httpx instrumentation not available (optional)")
                logger.info("✅ HTTP instrumentation enabled (requests + optional httpx)")
            except Exception as http_error:
                logger.warning(f"⚠️  Failed to enable HTTP instrumentation: {http_error}")
        else:
            logger.warning("⚠️  Application Insights connection string not found")
            logger.warning("   Tracing and Application Analytics will not work")
        
        # Create sub-agents
        mcp_endpoint = os.getenv("MCP_ENDPOINT")
        
        # 1. Tool Agent (MCP)
        logger.info(f"Creating Tool Agent (MCP: {mcp_endpoint})...")
        tool_agent = ToolAgent(project_client=project_client, mcp_endpoint=mcp_endpoint)
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
    """Root endpoint"""
    return {
        "status": "running",
        "service": "Agent API Server",
        "agents": {
            "main_agent": main_agent is not None,
            "tool_agent": tool_agent is not None,
            "research_agent": research_agent is not None
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Agent API Server"
    }

@app.post("/chat", response_model=AgentResponse)
async def chat_with_main_agent(request: AgentRequest):
    """Chat with the main agent"""
    if not main_agent:
        raise HTTPException(status_code=503, detail="Main agent not initialized")
    
    try:
        # ========================================================================
        # 🔍 OpenTelemetry Span for Tracing Input/Output
        # ========================================================================
        # Create a custom span to capture input/output in Azure AI Foundry Tracing
        # This makes the input/output columns visible in the Tracing UI
        # ========================================================================
        from opentelemetry import trace
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("agent_chat") as span:
            # Log input to span attributes (visible in Tracing)
            # Using Gen AI semantic conventions for Azure AI Foundry compatibility
            span.set_attribute("gen_ai.prompt", mask_text(request.message))
            span.set_attribute("gen_ai.system", "azure_ai_agent")
            # Get model deployment name from environment variable (default: gpt-5)
            model_name = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-5")
            span.set_attribute("gen_ai.request.model", model_name)
            
            logger.info(f"💬 Main Agent request: {request.message[:100]}...")
            
            response_text = await main_agent.run(
                message=request.message,
                thread_id=request.thread_id
            )
            
            # Log output to span attributes (visible in Tracing)
            # Using Gen AI semantic conventions for Azure AI Foundry compatibility
            span.set_attribute("gen_ai.completion", mask_text(response_text))
            span.set_attribute("gen_ai.response.finish_reason", "stop")
            
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
