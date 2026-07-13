import os
import json
from typing import TypedDict, Annotated, List, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool

# Load environment variable explicitly or let LangChain handle it if GROQ_API_KEY is in env
groq_api_key = os.environ.get("GROQ_API_KEY", "")

# Define State
class AgentState(TypedDict):
    messages: Annotated[list, "The messages in the conversation"]
    current_form_state: dict
    missing_fields: list
    suggested_follow_ups: list

# Tools Definition
@tool
def log_interaction(topics_discussed: str, sentiment: str, outcomes: str, materials_shared: str = "", samples_distributed: str = "") -> str:
    """Logs the interaction details after extracting them from the conversation."""
    return f"Logged: topics={topics_discussed}, sentiment={sentiment}, outcomes={outcomes}"

@tool
def edit_interaction(field_name: str, new_value: str) -> str:
    """Allows the LLM to modify previously extracted fields if the user corrects them in the chat."""
    return "Updated field " + field_name + " to " + new_value

@tool
def fetch_hcp_profile(hcp_id: int) -> str:
    """Dummy function returning HCP rules (e.g., sample limits)."""
    return json.dumps({"preferred_brand": "BrandX", "sample_restrictions": "Max 5 samples per visit"})

@tool
def check_compliance_limits(samples_requested: int, hcp_id: int) -> str:
    """Validates if the requested sample drop exceeds legal limits."""
    # Dummy check
    if samples_requested > 5:
        return "Warning: Requested samples exceed the compliance limit of 5."
    return "Compliance check passed."

@tool
def generate_follow_up_suggestions(conversation_summary: str) -> list:
    """Analyzes the conversation and outputs 2-3 specific, actionable next steps."""
    return [
        "+ Schedule follow-up meeting in 2 weeks",
        "+ Send product literature for BrandX",
        "+ Log a task to verify sample delivery"
    ]

tools = [log_interaction, edit_interaction, fetch_hcp_profile, check_compliance_limits, generate_follow_up_suggestions]

def create_agent():
    # Target model: gemma2-9b-it, fallback: llama-3.3-70b-versatile
    try:
        llm = ChatGroq(model="gemma2-9b-it", temperature=0)
    except Exception:
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        
    llm_with_tools = llm.bind_tools(tools)

    def chatbot(state: AgentState):
        messages = state["messages"]
        response = llm_with_tools.invoke(messages)
        
        # Simple extraction logic (in a real app we'd use structured output)
        # Here we attempt to map tool calls to state updates
        new_state = {**state}
        new_state["messages"] = messages + [response]
        
        return new_state

    # Tool execution node
    tool_node = ToolNode(tools)

    # Conditional edge
    def should_continue(state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return END

    def format_final_output(state: AgentState):
        # In a real scenario, this node would enforce strict JSON formatting
        # mapping the LLM's understanding into current_form_state.
        # For demonstration, we'll dummy some state extraction if there are tool calls.
        messages = state["messages"]
        last_ai_msg = [m for m in messages if isinstance(m, AIMessage)]
        if last_ai_msg:
            # We mock the structured output extraction
            state["suggested_follow_ups"] = [
                "+ Schedule follow-up meeting in 2 weeks",
                "+ Send additional clinical data"
            ]
            # Mock sentiment extraction
            text_content = str(last_ai_msg[-1].content).lower()
            if "positive" in text_content or "great" in text_content:
                state["current_form_state"]["sentiment"] = "Positive"
            elif "negative" in text_content or "bad" in text_content:
                state["current_form_state"]["sentiment"] = "Negative"
            else:
                state["current_form_state"]["sentiment"] = "Neutral"
                
            state["current_form_state"]["outcomes"] = "Discussed new product features."
        return state

    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_node("tools", tool_node)
    graph_builder.add_node("format", format_final_output)
    
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_conditional_edges("chatbot", should_continue, {"tools": "tools", END: "format"})
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_edge("format", END)

    return graph_builder.compile()

graph = create_agent()

def run_agent(message: str, current_form_state: dict):
    state = AgentState(
        messages=[HumanMessage(content=message)],
        current_form_state=current_form_state,
        missing_fields=[],
        suggested_follow_ups=[]
    )
    result = graph.invoke(state)
    return {
        "updated_form_state": result["current_form_state"],
        "suggested_follow_ups": result["suggested_follow_ups"]
    }
