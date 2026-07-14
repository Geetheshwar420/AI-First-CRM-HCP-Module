import os
import json
import schemas
from typing import TypedDict, Annotated, List, Dict, Any, Optional
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
def log_interaction(
    hcp_name: Optional[str] = None,
    interaction_type: Optional[str] = None,
    topics_discussed: Optional[str] = None,
    materials_shared: Optional[str] = None,
    samples_distributed: Optional[str] = None,
    sentiment: Optional[str] = None,
    outcomes: Optional[str] = None,
) -> str:
    """Logs the interaction details after extracting them from the conversation. Only provide fields explicitly mentioned. 'sentiment' MUST be Positive, Neutral, or Negative."""
    return "Logged."

@tool
def edit_interaction(field_name: str, new_value: str) -> str:
    """Allows the LLM to modify previously extracted fields if the user corrects them in the chat. field_name must match the schema keys."""
    return f"Updated field {field_name} to {new_value}"

from database import SessionLocal
import models
from datetime import datetime

@tool
def fetch_hcp_profile(hcp_name: str) -> str:
    """Retrieves HCP context and rules (e.g., preferences, sample limits) given their name."""
    db = SessionLocal()
    try:
        # Simple fuzzy search
        profile = db.query(models.HCPProfile).filter(models.HCPProfile.name.ilike(f"%{hcp_name}%")).first()
        if profile:
            return json.dumps({
                "specialty": profile.specialty,
                "preferred_brand": profile.preferred_brand,
                "sample_restrictions": profile.sample_restrictions,
                "has_sample_restrictions": profile.has_sample_restrictions
            })
        return json.dumps({"error": "HCP not found"})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        db.close()

@tool
def check_compliance_limits(product_name: str, samples_requested: str, hcp_name: Optional[str] = None) -> str:
    """Validates if the requested sample drop exceeds legal limits. Provide product_name and samples as a number string."""
    db = SessionLocal()
    try:
        requested = int(samples_requested)
    except ValueError:
        requested = 0
        
    try:
        # 1. Check HCP Restrictions
        if hcp_name:
            profile = db.query(models.HCPProfile).filter(models.HCPProfile.name.ilike(f"%{hcp_name}%")).first()
            if profile and profile.has_sample_restrictions:
                return json.dumps({"allowed": False, "reason": "HCP has a strict no-sample policy.", "remaining_allowance": 0})
        
        # 2. Check Product Limits
        product = db.query(models.Product).filter(models.Product.name.ilike(f"%{product_name}%")).first()
        if not product:
            return json.dumps({"allowed": False, "reason": f"Product '{product_name}' not found in database.", "remaining_allowance": 0})
            
        limit = product.monthly_sample_limit
        
        # 3. Calculate current drops this month
        current_month = datetime.now().strftime("%Y-%m")
        logs = db.query(models.SampleDistributionLog).join(models.HCPProfile).filter(
            models.HCPProfile.name.ilike(f"%{hcp_name}%") if hcp_name else True,
            models.SampleDistributionLog.product_id == product.id,
            models.SampleDistributionLog.date.startswith(current_month)
        ).all()
        
        already_dropped = sum(log.quantity for log in logs)
        
        if already_dropped + requested > limit:
            return json.dumps({
                "allowed": False, 
                "reason": f"Warning: You cannot leave {requested} samples. The legal monthly limit for {product.name} is {limit}. {already_dropped} already dropped this month.", 
                "remaining_allowance": max(0, limit - already_dropped)
            })
            
        return json.dumps({"allowed": True, "reason": "Compliance check passed.", "remaining_allowance": limit - already_dropped - requested})
    except Exception as e:
        return json.dumps({"allowed": False, "reason": f"System error during compliance check: {e}"})
    finally:
        db.close()

@tool
def generate_follow_up_suggestions(hcp_name: str, conversation_summary: str) -> str:
    """Analyzes the conversation and retrieves existing open tasks from the database for the HCP."""
    db = SessionLocal()
    try:
        profile = db.query(models.HCPProfile).filter(models.HCPProfile.name.ilike(f"%{hcp_name}%")).first()
        suggestions = []
        if profile:
            tasks = db.query(models.Task).filter(models.Task.hcp_id == profile.id, models.Task.status == "Open").all()
            for t in tasks:
                suggestions.append(f"Follow up on existing task: {t.description} (Due: {t.due_date})")
                
        # Generate some dynamic suggestions based on summary
        if "sample" in conversation_summary.lower():
            suggestions.append("+ Log a task to verify sample delivery")
        if "literature" in conversation_summary.lower() or "brochure" in conversation_summary.lower():
            suggestions.append("+ Send requested product literature")
        if not suggestions:
            suggestions.append("+ Schedule follow-up meeting in 2 weeks")
            
        return json.dumps(suggestions)
    except Exception as e:
        return json.dumps([f"Error generating suggestions: {e}"])
    finally:
        db.close()

tools = [log_interaction, edit_interaction, fetch_hcp_profile, check_compliance_limits, generate_follow_up_suggestions]

def create_agent():
    # Validate GROQ_API_KEY
    if not os.environ.get("GROQ_API_KEY"):
        raise ValueError("GROQ_API_KEY environment variable is missing. Please configure it.")
        
    # Target model: llama-3.3-70b-versatile
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        
    llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)

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
        
        # Parse tool calls to update state instead of making a second LLM call (Saves Tokens & respects architecture)
        for m in messages:
            # Check for AI tool calls
            if hasattr(m, 'tool_calls') and m.tool_calls:
                for tc in m.tool_calls:
                    name = tc.get('name')
                    args = tc.get('args', {})
                    if name == 'log_interaction':
                        for k, v in args.items():
                            if v and str(v).strip():
                                if k == 'sentiment':
                                    v = str(v).title()
                                state["current_form_state"][k] = v
                    elif name == 'edit_interaction':
                        field = args.get('field_name')
                        val = args.get('new_value')
                        if field and val:
                            if field == 'sentiment':
                                val = str(val).title()
                            state["current_form_state"][field] = val
                            
            # Check for ToolMessage results
            if getattr(m, 'type', None) == 'tool':
                if m.name == 'generate_follow_up_suggestions':
                    try:
                        import json
                        parsed_list = json.loads(m.content)
                        if isinstance(parsed_list, list):
                            state["suggested_follow_ups"] = parsed_list
                    except Exception:
                        state["suggested_follow_ups"] = [m.content]
                        
            # If hcp_name is passed to any tool (like check_compliance_limits or fetch_hcp_profile), capture it in form state
            if hasattr(m, 'tool_calls') and m.tool_calls:
                for tc in m.tool_calls:
                    if 'hcp_name' in tc.get('args', {}):
                        state["current_form_state"]["hcp_name"] = tc["args"]["hcp_name"]
                        
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
        "3. If PHYSICAL SAMPLES are distributed, use check_compliance_limits. Do NOT use this for emails or PDFs.\n"
        "4. Extract follow-up intents and dates using generate_follow_up_suggestions.\n"
        "5. If the user provides interaction details (topics, sentiment, materials, samples), use log_interaction to log them.\n"
        "6. If the user corrects previously provided details, use edit_interaction to update them.\n"
        "7. If no tools are needed, answer the user directly. CALL ONLY ONE TOOL AT A TIME."
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
