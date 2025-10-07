"""
Comprehensive Test Suite for Main Agent Workflow
Tests various routing scenarios and handoff patterns
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from main_agent_workflow import MainAgentWorkflow

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkflowTestSuite:
    """Test suite for workflow orchestration."""
    
    def __init__(self):
        """Initialize test suite."""
        self.orchestrator = MainAgentWorkflow()
        self.passed = 0
        self.failed = 0
        self.test_results = []
    
    async def run_test(self, test_name: str, user_input: str, expected_keywords: list) -> bool:
        """
        Run a single test case.
        
        Args:
            test_name: Name of the test
            user_input: User input to test
            expected_keywords: Keywords that should appear in response
            
        Returns:
            True if test passed, False otherwise
        """
        print("\n" + "=" * 80)
        print(f"Test: {test_name}")
        print("=" * 80)
        print(f"Input: {user_input}")
        
        try:
            response = await self.orchestrator.run(user_input)
            print(f"\nResponse:\n{response}\n")
            
            # Check if expected keywords are in response
            passed = True
            for keyword in expected_keywords:
                if keyword.lower() not in response.lower():
                    print(f"❌ Expected keyword missing: {keyword}")
                    passed = False
            
            if passed:
                print(f"✅ {test_name} PASSED")
                self.passed += 1
                self.test_results.append((test_name, "PASSED", response[:100]))
            else:
                print(f"❌ {test_name} FAILED")
                self.failed += 1
                self.test_results.append((test_name, "FAILED", response[:100]))
            
            return passed
            
        except Exception as e:
            logger.error(f"❌ Test error: {e}")
            print(f"❌ {test_name} FAILED with exception: {e}")
            self.failed += 1
            self.test_results.append((test_name, "FAILED", str(e)))
            return False
    
    async def run_all_tests(self):
        """Run all test scenarios."""
        print("\n" + "🧪" * 40)
        print("WORKFLOW ORCHESTRATION TEST SUITE")
        print("🧪" * 40 + "\n")
        
        # ===== TEST 1: TOOL AGENT (Weather) =====
        print("\n" + "🔧" * 40)
        print("TEST 1: TOOL AGENT - WEATHER QUERY")
        print("🔧" * 40)
        
        await self.run_test(
            "Weather Query Test",
            "What's the weather in Seoul?",
            ["tool", "seoul", "weather"]
        )
        
        # ===== TEST 2: RESEARCH AGENT (RAG) =====
        print("\n" + "📚" * 40)
        print("TEST 2: RESEARCH AGENT - RAG CONCEPT")
        print("📚" * 40)
        
        await self.run_test(
            "RAG Knowledge Test",
            "What is RAG and how does it work?",
            ["rag"]
        )
        
        # ===== TEST 3: MIXED (Weather + RAG) =====
        print("\n" + "🔀" * 40)
        print("TEST 3: MIXED ROUTING - WEATHER + KNOWLEDGE")
        print("🔀" * 40)
        
        await self.run_test(
            "Mixed Weather + Knowledge Test",
            "What's the weather in Tokyo and can you explain how AI agents use weather data in RAG systems?",
            []  # Should route to both tool and research agents
        )
        
        # ===== PRINT SUMMARY =====
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"Pass Rate: {pass_rate:.1f}%\n")
        
        if self.failed > 0:
            print("Failed Tests:")
            for name, status, detail in self.test_results:
                if status == "FAILED":
                    print(f"  ❌ {name}")
                    print(f"     {detail[:80]}...")
        
        print("\n" + "=" * 80)
        
        if self.failed == 0:
            print("🎉 ALL TESTS PASSED! 🎉")
        else:
            print(f"⚠️  {self.failed} test(s) need attention")
        
        print("=" * 80 + "\n")


async def run_quick_tests():
    """Run a quick subset of important tests."""
    print("\n" + "⚡" * 40)
    print("QUICK TEST SUITE (Essential Tests Only)")
    print("⚡" * 40 + "\n")
    
    orchestrator = MainAgentWorkflow()
    
    tests = [
        ("Weather", "What's the weather in Seoul?"),
        ("RAG", "What is RAG?"),
        ("Greeting", "Hello!"),
        ("Calculation", "Calculate 10 + 20"),
        ("Time", "What time is it?"),
    ]
    
    for name, query in tests:
        print(f"\n{'='*60}")
        print(f"Test: {name}")
        print(f"{'='*60}")
        print(f"Query: {query}\n")
        
        response = await orchestrator.run(query)
        print(f"Response: {response[:200]}...\n")


async def run_interactive_test():
    """Run interactive test mode."""
    orchestrator = MainAgentWorkflow()
    await orchestrator.run_interactive()


async def main():
    """Main test runner."""
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        
        if mode == "quick":
            await run_quick_tests()
        elif mode == "interactive":
            await run_interactive_test()
        elif mode == "full":
            suite = WorkflowTestSuite()
            await suite.run_all_tests()
        else:
            print("Usage:")
            print("  python3 test_workflow.py           # Run full test suite")
            print("  python3 test_workflow.py quick     # Run quick tests")
            print("  python3 test_workflow.py interactive # Run interactive mode")
            print("  python3 test_workflow.py full      # Run full test suite")
    else:
        # Default: run full test suite
        suite = WorkflowTestSuite()
        await suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
