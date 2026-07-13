# AI-First CRM: HCP Interaction Module

An intelligent, AI-powered Customer Relationship Management (CRM) module specifically designed for Life Sciences and Pharma Field Representatives. This system leverages Large Language Models (LLMs) to seamlessly bridge unstructured conversational data (voice notes, chat logs) with a highly structured relational database for logging Healthcare Professional (HCP) interactions.

## 🚀 Key Features

* **Dual-Mode Input:** Log interactions via a traditional structured form OR a conversational AI chat interface.
* **Real-time Form Sync:** Chat inputs automatically extract entities (HCP Name, Topics, Sentiment, Materials) and populate the React form in real-time.
* **Agentic AI Workflow:** Powered by LangGraph, the system intelligently selects tools to execute backend tasks based on user intent.
* **Medical Compliance Verification:** Automated, real-time checks against legal and PhRMA guidelines (e.g., sample dropping limits) before committing to the database.
* **Proactive Context:** The AI fetches and presents relevant HCP history and preferences before the meeting begins.
* **Smart Follow-ups:** One-click AI-suggested follow-up actions and task scheduling.

## 🏗️ Architecture & Tech Stack

This project follows a decoupled, asynchronous architecture optimized for real-time AI processing.

* **Frontend:**
  * React.js
  * Redux Toolkit (State Management)
  * Tailwind CSS (Styling)
  * Lucide-React (Icons)
  * Font: Google Inter

* **Backend:**
  * Python 3.10+
  * FastAPI (REST APIs & WebSocket support)
  * SQLAlchemy (ORM)
  * PostgreSQL / MySQL (Database)

* **AI & Orchestration:**
  * LangGraph (State Machine / Agent Orchestration)
  * LangChain (Tool binding)
  * Groq API (`gemma2-9b-it` for rapid extraction, `llama-3.3-70b-versatile` for deep context)

## 🧠 LangGraph Tooling

The AI Agent is equipped with five core tools to manage the sales workflow:

1. `log_interaction`: Parses conversational text to map and commit interaction data to the database.
2. `edit_interaction`: Modifies existing records based on conversational corrections (e.g., "Wait, I actually left 5 samples, not 3").
3. `fetch_hcp_profile`: Retrieves HCP context (specialty, restrictions, preferred products) to guide the LLM.
4. `check_compliance_limits`: Validates actions against medical compliance thresholds.
5. `schedule_follow_up`: Analyzes intents to create calendar events and actionable next steps.

## 🛠️ Local Development Setup

### Prerequisites
* Python 3.10+
* Node.js 18+
* PostgreSQL or MySQL server running locally
* Groq API Key

### Backend Setup (FastAPI + LangGraph)

1. Navigate to the backend directory:
   
```bash
   cd backend
   

```

2. Create and activate a virtual environment:

```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   

```

3. Install dependencies:

```bash
   pip install -r requirements.txt
   

```

4. Configure Environment Variables:
Create a `.env` file in the `backend` root and add your keys:

```env
   GROQ_API_KEY=your_groq_api_key_here
   DATABASE_URL=postgresql://user:password@localhost/crm_db 
   # or mysql+pymysql://user:password@localhost/crm_db
   

```

5. Run Database Migrations:

```bash
   alembic upgrade head
   

```

6. Start the FastAPI server:

```bash
   uvicorn app.main:app --reload --port 8000
   

```

### Frontend Setup (React)

1. Navigate to the frontend directory:

```bash
   cd frontend
   

```

2. Install dependencies:

```bash
   npm install
   

```

3. Configure Environment Variables:
Create a `.env` file in the `frontend` root:

```env
   REACT_APP_API_URL=http://localhost:8000/api
   

```

4. Start the React development server:

```bash
   npm start
   

```

## 🧪 Testing

The project includes comprehensive test suites for the AI tools and UAT scenarios.

* **Run Backend Unit Tests:**

```bash
  cd backend
  pytest tests/test_crm_tools.py -v
  

```

* See `uat_test_cases.md` in the docs folder for user behavior testing scenarios.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.