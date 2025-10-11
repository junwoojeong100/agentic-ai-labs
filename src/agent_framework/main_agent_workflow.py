"""
Main Agent - Agent Framework Workflow Pattern Implementation
Multi-agent orchestration using workflow executors and handoff pattern
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

from azure.identity.aio import AzureCliCredential, ManagedIdentityCredential, ChainedTokenCredential
from agent_framework.azure import AzureAIAgentClient
from agent_framework import WorkflowBuilder, WorkflowContext, executor

# OpenTelemetry imports for tracing
from opentelemetry import trace
from azure.monitor.opentelemetry import configure_azure_monitor
from azure.ai.inference.tracing import AIInferenceInstrumentor

# Import MCP and Search utilities
from tool_agent import ToolAgent
from research_agent import ResearchAgent

# Import masking utility
from masking import mask_content

# Load environment
load_dotenv()

logger = logging.getLogger(__name__)


# ---- Message Types ----
@dataclass
class UserMessage:
    """User message wrapper for workflow."""
    text: str
    metadata: Optional[dict] = None


# ---- Agent Creation Helper ----
def create_agent_client() -> AzureAIAgentClient:
    """Create Azure AI Agent client with appropriate credential."""
    project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
    # Priority: Environment variable > Default fallback
    # Use the same environment variable as foundry_agent for consistency
    model_deployment = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME")
    
    if not project_endpoint:
        raise ValueError(
            "AZURE_AI_PROJECT_ENDPOINT not set. "
            "Please set it in .env file or environment variables."
        )
    
    if not model_deployment:
        logger.warning(
            "AZURE_AI_MODEL_DEPLOYMENT_NAME not set. "
            "Please set it in .env file. Using 'gpt-5' as fallback."
        )
        model_deployment = "gpt-5"
    
    # Use ChainedTokenCredential to support both local dev and Container Apps
    # 1. Try Managed Identity (for Container Apps deployment)
    # 2. Fall back to Azure CLI (for local development)
    credential = ChainedTokenCredential(
        ManagedIdentityCredential(),
        AzureCliCredential()
    )
    
    return AzureAIAgentClient(
        project_endpoint=project_endpoint,
        model_deployment_name=model_deployment,
        async_credential=credential,
    )


# ---- Global Agent Instances (Lazy Initialization) ----
agent_client = None
router_agent = None
general_agent = None
tool_agent_instance = None
research_agent_instance = None


def _initialize_agents():
    """Initialize all agents (called on first use)."""
    global agent_client, router_agent, general_agent, tool_agent_instance, research_agent_instance
    
    if agent_client is not None:
        return  # Already initialized
    
    logger.info("Initializing agents...")
    
    # ========================================================================
    # 🔍 Step 1: Configure Azure Monitor for Observability (MUST BE FIRST!)
    # ========================================================================
    # This must be called BEFORE creating any Azure AI clients
    # to ensure all telemetry is properly captured
    # ========================================================================
    try:
        app_insights_conn = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        if app_insights_conn:
            configure_azure_monitor()
            logger.info("✅ Azure Monitor configured for observability")
            
            # Step 2: Instrument AI Inference for automatic LLM call tracing
            AIInferenceInstrumentor().instrument()
            logger.info("✅ AI Inference instrumentation enabled")
        else:
            logger.warning("⚠️  APPLICATIONINSIGHTS_CONNECTION_STRING not set - Observability disabled")
    except Exception as e:
        logger.warning(f"⚠️  Failed to configure observability: {e}")
    
    # Create agent client WITH logging enabled for tracing
    agent_client = create_agent_client()
    
    # Router Agent - Intelligent intent classifier with detailed agent capabilities
    router_agent = agent_client.create_agent(
        name="RouterAgent",
        instructions=(
            "Route user queries to the appropriate agent.\n\n"
            "AGENTS:\n"
            "• tool - Weather info via MCP (get_weather)\n"
            "• research - Knowledge search via RAG (Agent/MCP/RAG/Azure AI/Deployment)\n"
            "• orchestrator - Complex queries needing both tool + research\n"
            "• general - Casual conversation\n\n"
            "ROUTING:\n"
            "1. Weather queries → tool\n"
            "2. Knowledge questions (what/how/explain) → research\n"
            "3. Both weather + knowledge → orchestrator\n"
            "4. Greetings/casual → general\n\n"
            "EXAMPLES:\n"
            "Tokyo weather + explain MCP → orchestrator\n"
            "Seoul weather? → tool\n"
            "What is RAG? → research\n"
            "Hello → general\n"
            "Q: Thanks for your help! → general\n\n"
            "Respond with ONLY ONE WORD: orchestrator, tool, research, or general"
        ),
    )
    
    # General Agent - Handles casual conversation
    general_agent = agent_client.create_agent(
        name="GeneralAgent",
        instructions=(
            "You are a friendly general assistant for casual conversation.\n"
            "Handle greetings, simple questions, and general chat.\n"
            "Be concise, friendly, and helpful."
        ),
    )
    
    # Tool Agent - Create for MCP tool operations
    if os.getenv("MCP_ENDPOINT"):
        logger.info("Creating Tool Agent...")
        tool_agent_instance = ToolAgent(
            project_endpoint=os.getenv("AZURE_AI_PROJECT_ENDPOINT"),
            mcp_endpoint=os.getenv("MCP_ENDPOINT")
        )
    else:
        logger.warning("MCP_ENDPOINT not set - Tool Agent disabled")
    
    # Research Agent - Create for RAG operations  
    if os.getenv("SEARCH_ENDPOINT") and os.getenv("SEARCH_INDEX"):
        logger.info("Creating Research Agent...")
        search_key = os.getenv("SEARCH_KEY")
        if not search_key:
            logger.warning("⚠️  SEARCH_KEY not set - Research Agent will have limited functionality")
        
        research_agent_instance = ResearchAgent(
            project_endpoint=os.getenv("AZURE_AI_PROJECT_ENDPOINT"),
            search_endpoint=os.getenv("SEARCH_ENDPOINT"),
            search_index=os.getenv("SEARCH_INDEX"),
            search_key=search_key
        )
    else:
        logger.warning("SEARCH_ENDPOINT/SEARCH_INDEX not set - Research Agent disabled")
    
    logger.info("✅ All agents initialized")


# ---- Workflow Executors (Nodes) ----

@executor(id="router")
async def router_node(msg: UserMessage, ctx: WorkflowContext[UserMessage]) -> None:
    """
    Router executor: Simple rule-based + AI routing.
    """
    _initialize_agents()  # Ensure agents are initialized
    
    # ========================================================================
    # 🔍 OpenTelemetry Span for Router Execution Tracing
    # ========================================================================
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("workflow.router") as span:
        span.set_attribute("router.input", mask_content(msg.text))
        span.set_attribute("workflow.stage", "routing")
        
        logger.info(f"🔀 Router: Analyzing query")
        
        try:
            text_lower = msg.text.lower()
            
            # Weather-focused keywords (nouns only)
            tool_keywords = [
                "weather", "temperature", "temp", "forecast", "climate",
                "rain", "snow", "sun", "cloud", "wind", "humidity",
                "storm", "thunder", "fog", "degree", "celsius", "fahrenheit",
                "날씨", "기온", "온도", "일기예보"
            ]
            
            
            # Knowledge-focused keywords (nouns only)
            research_keywords = [
                # Core concepts
                "mcp", "protocol", "rag", "retrieval", "embedding", "vector",
                "agent", "orchestration", "handoff", "delegation",
                
                # Azure services
                "azure", "foundry", "search", "index", "openai", "llm",
                
                # Technical terms
                "architecture", "pattern", "deployment", "container", "docker",
                "thread", "tool", "function", "instruction", "prompt",
                
                # Korean terms
                "에이전트", "멀티", "검색", "배포", "아키텍처", "지식"
            ]
            
            orchestrator_keywords = [" and ", " also ", " plus ", " additionally ", " moreover "]
            
            # Check for keywords
            has_tool = any(kw in text_lower for kw in tool_keywords)
            has_research = any(kw in text_lower for kw in research_keywords)
            has_connector = any(kw in text_lower for kw in orchestrator_keywords)
            
            # Enhanced rule: If has both intentions with connecting words → orchestrator
            if has_tool and has_research and has_connector:
                logger.info(f"🎯 Rule-based routing → ORCHESTRATOR (detected: tool + research + connector)")
                span.set_attribute("router.method", "rule_based")
                span.set_attribute("router.intent", "orchestrator")
                span.set_attribute("router.reason", "multi_intent_with_connector")
                await ctx.send_message(msg, target_id="orchestrator")
                return
            
            # If clearly only tool keywords (no research keywords)
            if has_tool and not has_research and len(msg.text.split()) < 15:
                logger.info(f"🎯 Rule-based routing → TOOL (detected: pure tool request)")
                span.set_attribute("router.method", "rule_based")
                span.set_attribute("router.intent", "tool")
                span.set_attribute("router.reason", "pure_tool_request")
                await ctx.send_message(msg, target_id="tool")
                return
            
            # Otherwise, ask AI router with enhanced context
            span.set_attribute("router.method", "ai_based")
            result = await router_agent.run(f"Route this query: {msg.text}")
            intent = str(result.text if hasattr(result, 'text') else result).strip().lower()
            
            logger.info(f"📊 AI routing → {intent.upper()}")
            span.set_attribute("router.intent", intent)
            span.set_attribute("router.query_length", len(msg.text))
            
            if "orchestrator" in intent:
                await ctx.send_message(msg, target_id="orchestrator")
            elif "tool" in intent:
                await ctx.send_message(msg, target_id="tool")
            elif "research" in intent:
                await ctx.send_message(msg, target_id="research")
            else:
                await ctx.send_message(msg, target_id="general")
            
            span.set_attribute("router.status", "success")
        
        except Exception as e:
            logger.error(f"❌ Router error: {e}")
            span.set_attribute("router.status", "error")
            span.set_attribute("error.message", str(e))
            span.record_exception(e)
            await ctx.yield_output(f"Error in routing: {str(e)}")


@executor(id="tool")
async def tool_node(msg: UserMessage, ctx: WorkflowContext[UserMessage]) -> None:
    """
    Tool executor that handles external tool operations via MCP.
    """
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("workflow.executor.tool") as span:
        span.set_attribute("executor.type", "tool")
        span.set_attribute("executor.input", mask_content(msg.text))
        
        logger.info(f"🔧 Tool Agent: Processing request")
        
        try:
            if tool_agent_instance:
                # Use pre-created agent instance
                if not tool_agent_instance.agent:
                    await tool_agent_instance.initialize()
                
                actual_result = await tool_agent_instance.run(msg.text)
                span.set_attribute("executor.result_length", len(actual_result))
                span.set_attribute("executor.status", "success")
                await ctx.yield_output(f"🔧 [Tool Agent]\n{actual_result}")
            else:
                span.set_attribute("executor.status", "disabled")
                await ctx.yield_output(f"⚠️ Tool Agent: MCP endpoint not configured")
        
        except Exception as e:
            logger.error(f"❌ Tool node error: {e}")
            span.set_attribute("executor.status", "error")
            span.set_attribute("error.message", str(e))
            span.record_exception(e)
            await ctx.yield_output(f"Error in tool execution: {str(e)}")


@executor(id="research")
async def research_node(msg: UserMessage, ctx: WorkflowContext[UserMessage]) -> None:
    """
    Research executor that handles knowledge queries via RAG.
    """
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("workflow.executor.research") as span:
        span.set_attribute("executor.type", "research")
        span.set_attribute("executor.input", mask_content(msg.text))
        
        logger.info(f"📚 Research Agent: Processing request")
        
        try:
            if research_agent_instance:
                # Use pre-created agent instance
                if not research_agent_instance.agent:
                    await research_agent_instance.initialize()
                
                actual_result = await research_agent_instance.run(msg.text)
                span.set_attribute("executor.result_length", len(actual_result))
                span.set_attribute("executor.status", "success")
                await ctx.yield_output(f"{actual_result}")
            else:
                span.set_attribute("executor.status", "disabled")
                await ctx.yield_output(f"⚠️ Research Agent: Search not configured")
        
        except Exception as e:
            logger.error(f"❌ Research node error: {e}")
            span.set_attribute("executor.status", "error")
            span.set_attribute("error.message", str(e))
            span.record_exception(e)
            await ctx.yield_output(f"Error in research: {str(e)}")


@executor(id="general")
async def general_node(msg: UserMessage, ctx: WorkflowContext[UserMessage]) -> None:
    """
    General executor that handles casual conversation.
    """
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("workflow.executor.general") as span:
        span.set_attribute("executor.type", "general")
        span.set_attribute("executor.input", mask_content(msg.text))
        
        logger.info(f"💬 General Agent: Processing request")
        
        try:
            result = await general_agent.run(msg.text)
            response = str(result.text if hasattr(result, 'text') else result)
            span.set_attribute("executor.result_length", len(response))
            span.set_attribute("executor.status", "success")
            await ctx.yield_output(f"💬 {response}")
        
        except Exception as e:
            logger.error(f"❌ General node error: {e}")
            span.set_attribute("executor.status", "error")
            span.set_attribute("error.message", str(e))
            span.record_exception(e)
            await ctx.yield_output(f"Error in general conversation: {str(e)}")


@executor(id="orchestrator")
async def orchestrator_node(msg: UserMessage, ctx: WorkflowContext[UserMessage]) -> None:
    """
    Orchestrator executor that handles complex requests requiring multiple agents.
    Executes tool and research agents in parallel and combines results.
    """
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("workflow.executor.orchestrator") as span:
        span.set_attribute("executor.type", "orchestrator")
        span.set_attribute("executor.input", mask_content(msg.text))
        span.set_attribute("orchestrator.parallel_execution", True)
        
        logger.info(f"🎯 Orchestrator: Processing complex request with multiple agents")
        
        try:
            mcp_endpoint = os.getenv("MCP_ENDPOINT")
            search_endpoint = os.getenv("SEARCH_ENDPOINT")
            search_index = os.getenv("SEARCH_INDEX")
            project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
            
            results = []
            
            # Execute tool and research agents in parallel
            async def run_tool():
                if not tool_agent_instance:
                    return "⚠️ Tool Agent: MCP endpoint not configured"
                try:
                    if not tool_agent_instance.agent:
                        await tool_agent_instance.initialize()
                    result = await tool_agent_instance.run(msg.text)
                    return f"🔧 [Tool Agent]\n{result}"
                except Exception as e:
                    logger.error(f"Tool agent error: {e}")
                    return f"⚠️ Tool Agent error: {str(e)}"
            
            async def run_research():
                if not research_agent_instance:
                    return "⚠️ Research Agent: Search not configured"
                try:
                    if not research_agent_instance.agent:
                        await research_agent_instance.initialize()
                    result = await research_agent_instance.run(msg.text)
                    return result
                except Exception as e:
                    logger.error(f"Research agent error: {e}")
                    return f"⚠️ Research Agent error: {str(e)}"
            
            # Run both agents in parallel with span tracking
            logger.info("🔄 Running Tool and Research agents in parallel...")
            
            with tracer.start_as_current_span("orchestrator.parallel_execution"):
                tool_result, research_result = await asyncio.gather(
                    run_tool(),
                    run_research(),
                    return_exceptions=True
                )
            
            # Handle exceptions
            if isinstance(tool_result, Exception):
                tool_result = f"⚠️ Tool Agent error: {str(tool_result)}"
            if isinstance(research_result, Exception):
                research_result = f"⚠️ Research Agent error: {str(research_result)}"
            
            # Combine results
            combined_output = f"{tool_result}\n\n{research_result}"
            
            span.set_attribute("orchestrator.result_length", len(combined_output))
            span.set_attribute("orchestrator.status", "success")
            
            logger.info("✅ Orchestrator: Combined results from both agents")
            await ctx.yield_output(combined_output)
        
        except Exception as e:
            logger.error(f"❌ Orchestrator error: {e}")
            span.set_attribute("orchestrator.status", "error")
            span.set_attribute("error.message", str(e))
            span.record_exception(e)
            await ctx.yield_output(f"Error in orchestration: {str(e)}")


# ---- Build Workflow ----
workflow = (
    WorkflowBuilder()
    .set_start_executor(router_node)
    .add_edge(router_node, tool_node)
    .add_edge(router_node, research_node)
    .add_edge(router_node, general_node)
    .add_edge(router_node, orchestrator_node)
    # Remove handback edges to avoid cycles - specialized nodes terminate
    .build()
)


# ---- Cleanup Function ----
async def cleanup_all_agents():
    """Clean up all agent instances."""
    logger.info("🧽 Cleaning up all agents...")
    
    # Cleanup Tool Agent
    if tool_agent_instance:
        try:
            await tool_agent_instance.cleanup()
            logger.info("✅ Tool Agent cleaned up")
        except Exception as e:
            logger.error(f"❌ Tool Agent cleanup error: {e}")
    
    # Cleanup Research Agent
    if research_agent_instance:
        try:
            await research_agent_instance.cleanup()
            logger.info("✅ Research Agent cleaned up")
        except Exception as e:
            logger.error(f"❌ Research Agent cleanup error: {e}")
    
    # Cleanup agent_client (manages router_agent and general_agent)
    try:
        await agent_client.close()
        logger.info("✅ Agent client closed (router_agent and general_agent cleaned up)")
    except Exception as e:
        logger.error(f"❌ Agent client cleanup error: {e}")
    
    logger.info("✅ All agents cleaned up")


# ---- Main Orchestrator Class ----
class MainAgentWorkflow:
    """
    Main Agent using Agent Framework Workflow pattern.
    Provides handoff orchestration via workflow executors.
    """
    
    def __init__(self):
        """Initialize the workflow orchestrator."""
        self.workflow = workflow
        self.name = "Main Agent Workflow"
        # Agents will be initialized on first run
    
    async def run(self, user_input: str) -> str:
        """
        Run the workflow with user input.
        
        Args:
            user_input: User's message
            
        Returns:
            Collected output from workflow execution
        """
        # ========================================================================
        # 🔍 Top-level OpenTelemetry Span for Complete Workflow Tracing
        # ========================================================================
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span("agent_framework.workflow") as workflow_span:
            workflow_span.set_attribute("workflow.type", "multi_agent")
            workflow_span.set_attribute("workflow.pattern", "executor_graph")
            workflow_span.set_attribute("user.message", mask_content(user_input))
            
            logger.info(f"💬 User: {user_input}")
            
            msg = UserMessage(text=user_input)
            outputs = []
            
            try:
                async for event in self.workflow.run_stream(msg):
                    # Check event type and extract output
                    output = None
                    
                    if hasattr(event, 'output') and event.output is not None:
                        output = event.output
                    elif hasattr(event, 'data') and event.data is not None:
                        output = event.data
                    
                    # Only append non-None, non-empty outputs
                    if output is not None and str(output).strip():
                        logger.info(f"📤 Output: {output}")
                        outputs.append(str(output))
                
                final_result = "\n".join(outputs) if outputs else "No response generated"
                
                workflow_span.set_attribute("workflow.status", "success")
                workflow_span.set_attribute("workflow.output_length", len(final_result))
                workflow_span.set_attribute("workflow.output_count", len(outputs))
                
                return final_result
            
            except Exception as e:
                logger.error(f"❌ Workflow error: {e}")
                workflow_span.set_attribute("workflow.status", "error")
                workflow_span.set_attribute("error.message", str(e))
                workflow_span.record_exception(e)
                return f"Error: {str(e)}"
    
    async def run_interactive(self):
        """Run interactive conversation loop."""
        print("\n" + "=" * 80)
        print("🤖 Agent Framework Multi-Agent Workflow")
        print("=" * 80)
        print("\nCapabilities:")
        print("  🔧 Tool operations (weather, calculations, time)")
        print("  📚 Knowledge queries (AI, RAG, MCP, agents)")
        print("  🎯 Complex requests (tool + knowledge combined)")
        print("  💬 General conversation")
        print("\nType 'exit' or 'quit' to end.\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("\n👋 Goodbye!")
                    break
                
                response = await self.run(user_input)
                print(f"\n{response}\n")
            
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                print(f"\n❌ Error: {e}\n")
