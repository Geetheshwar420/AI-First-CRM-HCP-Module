import os
import sys
import time
import pytest
from dotenv import load_dotenv

# 1. Force load the .env file dynamically BEFORE importing the agent code
load_dotenv()

# Adjust path context to properly find backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 2. Import run_agent safely now that environment variables exist
from agent import run_agent

# Global analytics collector for deployment report logs
TEST_REPORT_STATS = []

@pytest.fixture(scope="function", autouse=True)
def test_feedback_reporter(request):
    """Automatically logs execution time, status, and custom tool feedback messages."""
    start_time = time.time()
    yield
    duration = time.time() - start_time
    # Capture test outcome from the internal request node status
    report_status = "PASSED" if not hasattr(request.node, "rep_call") or request.node.rep_call.passed else "FAILED"
    
    stat_entry = {
        "name": request.node.name,
        "duration": f"{duration:.3f}s",
        "tool_targeted": request.node.name.replace("test_", "")
    }
    TEST_REPORT_STATS.append(stat_entry)
    
    # Sleep to prevent LLM API rate limit errors (Groq 429 Too Many Requests - 6000 TPM limit)
    time.sleep(15)


@pytest.fixture
def empty_form_state():
    return {
        "hcp_id": None,
        "hcp_name": None,
        "interaction_type": None,
        "date": None,
        "time": None,
        "attendees": None,
        "topics_discussed": None,
        "materials_shared": None,
        "samples_distributed": None,
        "sentiment": None,
        "outcomes": None,
        "follow_up_actions": None
    }


class TestLangGraphAgentTools:

    def test_tool_fetch_hcp_profile(self, empty_form_state):
        """Verifies that the agent calls fetch_hcp_profile when asked about HCP preferences."""
        message = "What are Dr. Lee's preferred products?"
        result = run_agent(message, empty_form_state)
        reply = result.get("reply_message", "").lower()
        
        assert "drug a" in reply or "drug c" in reply, f"Agent failed to fetch profile. Reply: {reply}"

    def test_tool_check_compliance_limits_violation(self, empty_form_state):
        """Verifies that dropping too many samples triggers the compliance warning tool."""
        message = "I want to leave 10 samples of OncoBoost with Dr. Smith today."
        result = run_agent(message, empty_form_state)
        reply = result.get("reply_message", "").lower()
        
        assert any(word in reply for word in ["warning", "limit", "allow", "5"]), f"Compliance tool was not triggered. Reply: {reply}"

    def test_log_interaction_extraction(self, empty_form_state):
        """Verifies structural text mapping correctly updates form states."""
        message = "Met with Dr. Sarah Jenkins today. We discussed the Phase 3 trial data for OncoBoost. She was very receptive. Left 2 brochures."
        result = run_agent(message, empty_form_state)
        form_state = result.get("updated_form_state", {})
        
        assert form_state.get("hcp_name") == "Dr. Sarah Jenkins", "HCP name entity extraction failed."
        assert "Phase 3" in form_state.get("topics_discussed", ""), "Topics mapping failed."
        assert form_state.get("sentiment") in ["Positive", "Neutral", "Receptive"], "Sentiment inference failed."
        
    def test_missing_hcp_guardrail(self, empty_form_state):
        """Verifies that missing mandatory fields causes the LLM to actively poll for information."""
        message = "Had a great meeting today discussing OncoBoost. They were very positive."
        result = run_agent(message, empty_form_state)
        reply = result.get("reply_message", "").lower()
        form_state = result.get("updated_form_state", {})
        
        assert "who" in reply or "name" in reply, f"Agent did not query missing field. Reply: {reply}"
        assert form_state.get("hcp_name") is None, "Agent incorrectly hallucinated a name."

    def test_edit_interaction_correction(self):
        """Verifies multi-turn contextual state updates work appropriately."""
        existing_state = {
            "hcp_name": "Dr. Smith",
            "samples_distributed": "3",
            "sentiment": "Neutral"
        }
        message = "Wait, my mistake, I actually left 5 samples, not 3. And he was actually very Positive."
        result = run_agent(message, existing_state)
        updated_state = result.get("updated_form_state", {})
        
        assert "5" in str(updated_state.get("samples_distributed")), "Edit modification tool failed."
        assert updated_state.get("sentiment") == "Positive", "Sentiment rewrite tool failed."

    def test_generate_follow_up_suggestions(self, empty_form_state):
        """Checks if suggested follow ups are compiled inside the active processing node."""
        message = "I need to send Dr. Smith the clinical trial PDF next week."
        result = run_agent(message, empty_form_state)
        suggestions = result.get("suggested_follow_ups", [])
        
        assert len(suggestions) > 0, "No suggestions calculated by format node."
        assert isinstance(suggestions, list), "Format incorrect."


# ====================================================================
# Visual Pipeline Execution Summary Report Block
# ====================================================================
class AgentTestReportPlugin:
    """Custom Pytest Plugin to print the deployment summary at the end."""
    def pytest_sessionfinish(self, session, exitstatus):
        print("\n" + "="*80)
        print(" [REPORT] AI-FIRST CRM: MULTI-AGENT TOOL COMPLETION & DEPLOYMENT FEEDBACK REPORT")
        print("="*80)
        print(f"{'TEST CASE NAME':<45} | {'TARGETED TOOL':<22} | {'DURATION':<10}")
        print("-"*80)
        for entry in TEST_REPORT_STATS:
            print(f"{entry['name']:<45} | {entry['tool_targeted']:<22} | {entry['duration']:<10}")
        print("="*80)
        if exitstatus == 0:
            print(" [SUCCESS] STATUS: DEPLOYMENT SUCCESS - ALL LANGGRAPH CAPABILITIES OPERATIONAL")
        else:
            print(" [FAILED] STATUS: DEPLOYMENT BLOCKED - COMPLIANCE ENGINE CRASH DETECTED")
        print("="*80 + "\n")

if __name__ == "__main__":
    # Execute the tests programmatically when running this file as a standard Python script
    # e.g., `python langgraph_agent_integration_tests.py`
    sys.exit(pytest.main(["-v", "-s", __file__], plugins=[AgentTestReportPlugin()]))

