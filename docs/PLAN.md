# AI-First CRM HCP Module Implementation Plan

## Goal Description
Build an AI-First CRM HCP (Health Care Professional) Interaction Module. This includes a React/Redux frontend with an interaction logging UI and AI chat interface, a FastAPI/PostgreSQL backend for data persistence and API endpoints, and a LangGraph cognitive engine to process conversational input and map it to structured data.

## User Review Required
> [!IMPORTANT]
> Please review this orchestration plan. We are in Phase 1 (Planning). After your approval, I will proceed to Phase 2 and coordinate the implementation across the Frontend, Backend, and AI Engineer agents in parallel.

## Proposed Architecture and Domains

### 1. Frontend (React & Redux)
- **Tech Stack:** React, Redux Toolkit, Tailwind CSS, Lucide-React.
- **Tasks:**
  - Create the UI layout (65/35 split).
  - Left column: Structured form (HCP Name, Interaction Type, Date, Time, Attendees, Topics, Materials, Sentiment, Outcomes, Follow-up actions).
  - Right column: AI Assistant Chat.
  - Implement Redux `interactionSlice` to manage form state globally.
  - Integrate placeholder API calls to update the form state based on chat responses.

### 2. Backend (FastAPI & Database)
- **Tech Stack:** Python, FastAPI, SQLAlchemy, PostgreSQL/MySQL.
- **Tasks:**
  - Define Database Models (`HCPProfile`, `InteractionLog`, `Task`).
  - Create Pydantic schemas for data validation.
  - Implement API endpoints:
    - `POST /api/interactions`: Save structured form data.
    - `POST /api/chat`: Process natural language via LangGraph agent and return structured data.
    - `GET /api/hcp/{id}`: Fetch HCP details.

### 3. AI Cognitive Engine (LangGraph)
- **Tech Stack:** Python, LangGraph, Langchain, Groq API.
- **Tasks:**
  - Define `AgentState` TypedDict.
  - Create AI tools: `log_interaction`, `edit_interaction`, `fetch_hcp_profile`, `check_compliance_limits`, `generate_follow_up_suggestions`.
  - Build LangGraph state machine to route conversational input, execute tools, extract sentiment, and format output matching backend schema.

## Open Questions
> [!WARNING]
> 1. Should we create a new project directory for this, or use the root workspace directory? 
> 2. Do you have a specific database connection string for PostgreSQL/MySQL, or should we use SQLite for local development?
> 3. Do you have a valid Groq API key configured in the environment?

## Verification Plan
### Automated Tests
- Run backend unit tests for endpoints.
- Run schema validation checks.

### Manual Verification
- Start FastAPI server and verify Swagger UI docs.
- Start React frontend and interact with the UI.
- Verify that sending a chat message correctly populates the left-side form via the LangGraph engine.

## Orchestration Plan
Once approved, I will sequentially coordinate the agents to implement these components, followed by executing verification scripts (e.g., security scan, linting).
