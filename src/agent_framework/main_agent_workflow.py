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

# Import MCP and Search utilities
from tool_agent import ToolAgent
from research_agent import ResearchAgent

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
    model_deployment = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4o")
    
    if not project_endpoint:
        raise ValueError(
            "AZURE_AI_PROJECT_ENDPOINT not set. "
            "Please set it in .env file or environment variables."
        )
    
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
    
    # Create agent client
    agent_client = create_agent_client()
    
    # Router Agent - Simple intent classifier
    router_agent = agent_client.create_agent(
        name="RouterAgent",
        instructions=(
            "You are a simple router. Analyze the query and respond with ONLY ONE WORD.\n\n"
            "Rules:\n"
            "- If query needs BOTH (tool operation + knowledge): orchestrator\n"
            "- If query needs ONLY tool (weather/calc/time/random): tool\n"
            "- If query needs ONLY knowledge (RAG/MCP/AI concepts): research\n"
            "- If casual conversation: general\n\n"
            "Examples:\n"
            "Q: weather in Tokyo and what is MCP → orchestrator\n"
            "Q: weather in Seoul → tool\n"
            "Q: what is RAG → research\n"
            "Q: hello → general\n\n"
            "Respond with ONE WORD: orchestrator, tool, research, or general"
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
    
    logger.info(f"🔀 Router: Analyzing query")
    
    try:
        text_lower = msg.text.lower()
        
        # Simple rule-based detection
        tool_words = ["weather", "calculate", "time", "random"]
        research_words = ["what is", "explain", "how", "mcp", "rag", "agent", "protocol"]
        
        has_tool = any(w in text_lower for w in tool_words)
        has_research = any(w in text_lower for w in research_words)
        has_and = " and " in text_lower
        
        # Rule: If has both + 'and' → orchestrator
        if has_tool and has_research and has_and:
            logger.info(f"🎯 Rule-based routing → ORCHESTRATOR")
            await ctx.send_message(msg, target_id="orchestrator")
            return
        
        # Otherwise, ask AI router
        result = await router_agent.run(f"Route this: {msg.text}")
        intent = str(result.text if hasattr(result, 'text') else result).strip().lower()
        
        logger.info(f"📊 AI routing → {intent.upper()}")
        
        if "orchestrator" in intent:
            await ctx.send_message(msg, target_id="orchestrator")
        elif "tool" in intent:
            await ctx.send_message(msg, target_id="tool")
        elif "research" in intent:
            await ctx.send_message(msg, target_id="research")
        else:
            await ctx.send_message(msg, target_id="general")
    
    except Exception as e:
        logger.error(f"❌ Router error: {e}")
        await ctx.yield_output(f"Error in routing: {str(e)}")


@executor(id="tool")
async def tool_node(msg: UserMessage, ctx: WorkflowContext[UserMessage]) -> None:
    """
    Tool executor that handles external tool operations via MCP.
    """
    logger.info(f"🔧 Tool Agent: Processing request")
    
    try:
        if tool_agent_instance:
            # Use pre-created agent instance
            if not tool_agent_instance.agent:
                await tool_agent_instance.initialize()
            
            actual_result = await tool_agent_instance.run(msg.text)
            await ctx.yield_output(f"🔧 [Tool Agent]\n{actual_result}")
        else:
            await ctx.yield_output(f"⚠️ Tool Agent: MCP endpoint not configured")
    
    except Exception as e:
        logger.error(f"❌ Tool node error: {e}")
        await ctx.yield_output(f"Error in tool execution: {str(e)}")


@executor(id="research")
async def research_node(msg: UserMessage, ctx: WorkflowContext[UserMessage]) -> None:
    """
    Research executor that handles knowledge queries via RAG.
    """
    logger.info(f"📚 Research Agent: Processing request")
    
    try:
        if research_agent_instance:
            # Use pre-created agent instance
            if not research_agent_instance.agent:
                await research_agent_instance.initialize()
            
            actual_result = await research_agent_instance.run(msg.text)
            await ctx.yield_output(f"{actual_result}")
        else:
            await ctx.yield_output(f"⚠️ Research Agent: Search not configured")
    
    except Exception as e:
        logger.error(f"❌ Research node error: {e}")
        await ctx.yield_output(f"Error in research: {str(e)}")


@executor(id="general")
async def general_node(msg: UserMessage, ctx: WorkflowContext[UserMessage]) -> None:
    """
    General executor that handles casual conversation.
    """
    logger.info(f"💬 General Agent: Processing request")
    
    try:
        result = await general_agent.run(msg.text)
        response = str(result.text if hasattr(result, 'text') else result)
        await ctx.yield_output(f"💬 {response}")
    
    except Exception as e:
        logger.error(f"❌ General node error: {e}")
        await ctx.yield_output(f"Error in general conversation: {str(e)}")


@executor(id="orchestrator")
async def orchestrator_node(msg: UserMessage, ctx: WorkflowContext[UserMessage]) -> None:
    """
    Orchestrator executor that handles complex requests requiring multiple agents.
    Executes tool and research agents in parallel and combines results.
    """
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
        
        # Run both agents in parallel
        logger.info("🔄 Running Tool and Research agents in parallel...")
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
        
        logger.info("✅ Orchestrator: Combined results from both agents")
        await ctx.yield_output(combined_output)
    
    except Exception as e:
        logger.error(f"❌ Orchestrator error: {e}")
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
            
            return "\n".join(outputs) if outputs else "No response generated"
        
        except Exception as e:
            logger.error(f"❌ Workflow error: {e}")
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
