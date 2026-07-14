# AI-First CRM: HCP Interaction Module

An intelligent, AI-powered Customer Relationship Management (CRM) module specifically designed for Life Sciences and Pharma Field Representatives. This system leverages Large Language Models (LLMs) to seamlessly bridge unstructured conversational data (voice notes, chat logs) with a highly structured relational database for logging Healthcare Professional (HCP) interactions.

## 🚀 Key Features

* **Dual-Mode Input:** Log interactions via a traditional structured form OR a conversational AI chat interface.
* **Real-time Form Sync:** Chat inputs automatically extract entities (HCP Name, Topics, Sentiment, Materials) and populate the React form in real-time.
* **Agentic AI Workflow:** Powered by LangGraph, the system intelligently selects tools to execute backend tasks based on user intent.
* **Medical Compliance Verification:** Automated, real-time checks against legal and PhRMA guidelines (e.g., sample dropping limits) before committing to the database.
* **Proactive Context:** The AI fetches and presents relevant HCP history and preferences before the meeting begins.
* **Smart Follow-ups:** Dynamically queries the database for open tasks and generates actionable next steps based on interaction summaries.

## 🏗️ Architecture & Tech Stack

This project follows a decoupled, asynchronous architecture optimized for real-time AI processing, leveraging a strict tool-calling protocol for security and cost efficiency.

### Frontend
* **Framework:** React.js powered by Vite
* **Styling:** Tailwind CSS with custom aesthetic configuration
* **Icons:** Lucide-React
* **Typography:** Google Inter

### Backend
* **Framework:** FastAPI (Python 3.12+)
* **Database:** SQLite (local development) with SQLAlchemy ORM
* **Models:** Relational schema separating `HCPProfile`, `Product`, `SampleDistributionLog`, and `Task`

### AI Orchestration (LangGraph Core)
The AI pipeline is built on **LangGraph** and utilizes `ChatGroq` targeting the `llama-3.3-70b-versatile` model. 

#### Structural Optimizations
1. **Token Efficiency (`format_final_output`)**: Instead of relying on expensive LLM-based structured output parsing at the end of the graph, the orchestrator explicitly intercepts the AI's internal `tool_calls` dictionary and natively parses the Python payloads to push state updates into the frontend form.
2. **Parallel Tooling Disabled**: To prevent erratic hallucination payloads causing `400 Bad Request` exceptions against the LLM, `parallel_tool_calls` is explicitly disabled to enforce stable, sequential tool execution.

## 🧠 LangGraph Tooling

The AI Agent is equipped with five explicitly isolated tools to securely interact with the backend database. **CRITICALLY: These tools do not run automatically in the background or via middleware interceptors. They are 100% triggered by the AI's autonomous reasoning and decision-making capabilities based on the conversational context and strict system prompts.** By architectural design, the LLM NEVER runs direct DB execution without explicitly invoking these Python tool wrappers.

1. `log_interaction`: **(AI-Triggered)** A mandatory tool. Parses conversational text to map interaction data (topics, sentiment, materials) into the active CRM form state.
2. `edit_interaction`: **(AI-Triggered)** A mandatory tool. Re-runs mapping logic if a user verbally corrects themselves in the chat (e.g., "Wait, I actually left 5 samples, not 3").
3. `fetch_hcp_profile`: **(AI-Triggered)** Dynamically searched by the AI when it needs to inject rules, constraints (like strict "No Sample" policies), and context before generating a response.
4. `check_compliance_limits`: **(AI-Triggered)** Intelligently invoked by the AI whenever it detects physical sample drop commands. It runs mathematical aggregations against the `SampleDistributionLog` and `Product` tables to deny requests that violate PhRMA monthly limits.
5. `generate_follow_up_suggestions`: **(AI-Triggered)** Called by the AI at the conclusion of an interaction to query the `Task` table for existing open tasks and algorithmically generate context-aware suggestions (formatted as a strict JSON string for safe LangGraph extraction).

## 🧪 Integration Testing Pipeline

The backend includes a highly rigorous integration suite (`langgraph_agent_integration_tests.py`) designed to validate the strict behavioral boundaries of the LLM:

* **Entity Extraction Constraints:** Verifies the LLM maps explicit strings (e.g., "Positive", "Neutral", "Negative") to satisfy CRM Enums via `update_form` docstring strictness.
* **Compliance Blocking:** Simulates limit violations to ensure the LangGraph `check_compliance_limits` tool accurately overrides the AI's intent to distribute excessive samples.
* **Guardrail Enforcement:** Verifies the AI proactively prompts the user for missing mandatory fields (like HCP Name) before triggering interaction logs.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.