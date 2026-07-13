import os
import json
import schemas
from typing import TypedDict, Annotated, List, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool

from langgraph.graph.message import add_messages

# Load environment variable explicitly or let LangChain handle it if GROQ_API_KEY is in env
groq_api_key = os.environ.get("GROQ_API_KEY", "")

# Define State
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
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
def fetch_hcp_profile(hcp_name: str) -> str:
    """Retrieves HCP context and rules (e.g., preferences, sample limits) given their name."""
    # Dummy mock for UAT Scenario
    if "smith" in hcp_name.lower():
        return json.dumps({"specialty": "Oncologist", "preferred_brand": "OncoBoost", "sample_restrictions": "Strict no-sample policy"})
    elif "lee" in hcp_name.lower():
        return json.dumps({"preferred_brand": "Drug A and Drug C", "specialty": "General Practice"})
    return json.dumps({"preferred_brand": "BrandX", "sample_restrictions": "Max 5 samples per visit"})

@tool
def check_compliance_limits(samples_requested: int, hcp_id: Optional[int] = None) -> str:
    """Validates if the requested sample drop exceeds legal limits."""
    # Dummy check for UAT Scenario
    if samples_requested > 5:
        return f"Warning: You cannot leave {samples_requested} samples. The legal monthly limit is 5. Please adjust the quantity."
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
    # Validate GROQ_API_KEY
    if not os.environ.get("GROQ_API_KEY"):
        raise ValueError("GROQ_API_KEY environment variable is missing. Please configure it.")
        
    # Target model: llama-3.1-8b-instant, fallback: llama-3.3-70b-versatile
    try:
        llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
    except Exception:
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        
    llm_with_tools = llm.bind_tools(tools)

    def chatbot(state: AgentState):
        messages = state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    # Tool execution node
    tool_node = ToolNode(tools)

    # Conditional edge
    def should_continue(state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]
        
        # Safeguard: if there are more than 6 messages, force an end to prevent infinite loops (API cost saving)
        if len(messages) > 6:
            return END
            
        if last_message.tool_calls:
            return "tools"
        return END

    def format_final_output(state: AgentState):
        messages = state["messages"]
        print("MESSAGES TYPE AND CONTENT:", type(messages), messages)
        
        # Build conversation history for extraction
        convo_history = []
        for m in messages:
            if hasattr(m, 'type'):
                content = m.content
                if m.type == 'ai' and getattr(m, 'tool_calls', None):
                    content += " [Tool calls: " + str(m.tool_calls) + "]"
                convo_history.append(f"{m.type.upper()}: {content}")
            elif isinstance(m, dict):
                convo_history.append(f"{m.get('type', 'UNKNOWN').upper()}: {m.get('content', '')}")
            else:
                convo_history.append(f"{type(m).__name__.upper()}: {getattr(m, 'content', str(m))}")
                
        conversation_text = "\n".join(convo_history)
        print("CONVERSATION TEXT:", conversation_text)
        
        # Use LLM to extract the information into the schema
        extractor = llm.with_structured_output(schemas.InteractionBase)
        
        prompt = f"""You are an AI assistant. Extract the details from the full conversation history below and update the current CRM form state.
        Current State: {state.get('current_form_state', {})}
        
        Conversation History:
        {conversation_text}
        
        Output ONLY the fields that need to be updated based on the Conversation. If a field is not mentioned, leave it null/empty.
        For sentiment, use exactly 'Positive', 'Neutral', or 'Negative'.
        """
        
        try:
            print("Extracting with prompt:", prompt)
            extracted_update = extractor.invoke(prompt)
            print("Extracted update:", extracted_update.model_dump())
            # Merge the updates into the state
            for key, value in extracted_update.model_dump(exclude_unset=True, exclude_none=True).items():
                if value and str(value).strip():
                    state["current_form_state"][key] = value
        except Exception as e:
            print("Extraction error:", e)
            
        # Suggested follow ups
        state["suggested_follow_ups"] = [
            "+ Schedule follow-up meeting in 2 weeks",
            "+ Log a task to verify sample delivery"
        ]
        
        return state

    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_node("tools", tool_node)
    graph_builder.add_node("format", format_final_output)
    
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_conditional_edges("chatbot", should_continue, {"tools": "tools", END: "format"})
    # Re-enable standard ReAct loop: let tools return to chatbot so AI can observe output.
    # We rely on recursion_limit=4 and should_continue to prevent infinite looping.
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_edge("format", END)

    return graph_builder.compile()

graph = create_agent()

from langchain_core.messages import SystemMessage

def run_agent(message: str, current_form_state: dict):
    sys_prompt = (
        "You are an AI assistant for a CRM HCP module. Follow these rules STRICTLY:\n"
        "1. If the user is logging an interaction but omits the HCP Name, do NOT extract the data yet. Ask 'Who did you meet with?'.\n"
        "2. Answer questions about HCP preferences by using fetch_hcp_profile.\n"
        "3. If samples are dropped, use check_compliance_limits. If it returns a warning, relay that warning to the user.\n"
        "4. Extract follow-up intents and dates using generate_follow_up_suggestions.\n"
        "5. If no tools are needed, answer the user directly."
    )
    sys_msg = SystemMessage(content=sys_prompt)
    state = AgentState(
        messages=[sys_msg, HumanMessage(content=message)],
        current_form_state=current_form_state,
        missing_fields=[],
        suggested_follow_ups=[]
    )
    result = graph.invoke(state, {"recursion_limit": 10})
    
    reply_message = "Interaction processed."
    for m in reversed(result["messages"]):
        if hasattr(m, 'type') and m.type == 'ai' and not getattr(m, 'tool_calls', None) and m.content:
            reply_message = m.content
            break

    return {
        "updated_form_state": result.get("current_form_state", {}),
        "suggested_follow_ups": result.get("suggested_follow_ups", []),
        "reply_message": reply_message
    }
