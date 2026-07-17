# CareerForge — Local AI Career Toolkit

A fully local, AI-powered career assistant built on **Gemma 4 26B** (via Ollama), **LangGraph**, and **PostgreSQL**. No cloud LLM calls, no data leaving your machine.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend  (React + Vite)                    │
│  Sidebar nav → tool panels → fetch /api/* → render markdown     │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTP (proxied by Vite dev server)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend  (FastAPI + Python)                   │
│                                                                 │
│  Routes          →  LangGraph Workflows  →  Ollama (Gemma 4)   │
│  /api/analyze-job      Core Application Chain (3 nodes)         │
│  /api/career-advice    Strategic Sandbox (RAG + Gemma 4)        │
│  /api/cover-letter     Single-node prompt tools                 │
│  /api/networking-message                                        │
│  /api/skill-gap-plan                                            │
│  /api/company-research                                          │
│  /api/salary-negotiation                                        │
│  /api/mock-interview                                            │
│  /api/upload-resume    Extracts text → saves to DB              │
│  /api/resume-info      Returns current resume filename          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PostgreSQL + pgvector  (Docker)                 │
│                                                                 │
│  resumes table          — uploaded resume text (single row)     │
│  LangGraph checkpoints  — JSONB conversation state              │
│  career_knowledge       — pgvector embeddings for RAG           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Backend

### Stack
| Component | Technology |
|---|---|
| API framework | FastAPI |
| Orchestration | LangGraph |
| LLM | Gemma 4 26B via Ollama (`langchain-ollama`) |
| Embeddings | `nomic-embed-text` via Ollama |
| Vector store | pgvector via `langchain-postgres` |
| Checkpointing | LangGraph Postgres checkpointer |
| Database driver | psycopg3 (`psycopg[binary,pool]`) |
| Resume parsing | `python-docx`, `pypdf` |

### Structure
```
backend/
├── main.py                  # FastAPI app, lifespan, CORS, router registration
├── config.py                # Settings loaded from .env (pydantic-settings)
├── resume.py                # Resume DB table: setup, load, save, text extraction
├── llm.py                   # Shared ChatOllama instance
├── database/
│   └── connection.py        # Async pool, checkpointer, vector store singletons
├── state/
│   ├── application_state.py # TypedDict for the core application workflow
│   └── sandbox_state.py     # TypedDict for the career advisor workflow
├── nodes/
│   ├── jd_analyser.py       # Node 1: extract & structure the job description
│   ├── resume_optimizer.py  # Node 2: critique resume against JD
│   ├── interview_coach.py   # Node 3: STAR-method interview prep
│   └── career_advisor.py    # RAG node: vector search + Gemma 4 advice
├── workflows/
│   ├── core_application.py  # JD Analyser → Resume Optimizer → Interview Coach
│   └── strategic_sandbox.py # Career Advisor (single node)
└── api/routes/
    ├── analyze_job.py        # POST /api/analyze-job
    ├── career_advice.py      # POST /api/career-advice
    ├── resume_info.py        # GET /api/resume-info, POST /api/upload-resume
    ├── cover_letter.py       # POST /api/cover-letter
    ├── networking_message.py # POST /api/networking-message
    ├── skill_gap_plan.py     # POST /api/skill-gap-plan
    ├── company_research.py   # POST /api/company-research
    ├── salary_negotiation.py # POST /api/salary-negotiation
    └── mock_interview.py     # POST /api/mock-interview
```

### LangGraph Workflows

**Workflow 1 — Core Application Chain**
```
JD Analyser  →  Resume Optimizer  →  Interview Coach
   (text or image input)
```
Each node is an async function that reads from and writes to `ApplicationState`. The full chain runs sequentially; state is persisted in Postgres via the LangGraph checkpointer.

**Workflow 2 — Strategic Sandbox**
```
Career Advisor  (pgvector similarity search → Gemma 4)
```
Retrieves the top-4 most relevant chunks from the `career_knowledge` vector store and passes them as context to Gemma 4.

---

## Frontend

### Stack
| Component | Technology |
|---|---|
| Framework | React 18 |
| Build tool | Vite 8 |
| Styling | Tailwind CSS v4 |
| Markdown rendering | `react-markdown` |
| Language | TypeScript |

### Structure
```
frontend/src/
├── main.tsx                 # Entry point — mounts ToastProvider + SharedProvider + App
├── App.tsx                  # Sidebar nav + tool routing
├── shared.tsx               # React context: shared state across tools (jd_text, etc.)
├── hooks.ts                 # useLocalStorage, useElapsedSeconds
├── index.css                # Tailwind v4 theme tokens
└── components/
    ├── JobApplicationUI.tsx  # Paste/upload JD → analyse against resume
    ├── CareerAdvisorUI.tsx   # Free-form career query → RAG-backed advice
    ├── MockInterviewUI.tsx   # Mock interview session
    ├── PromptTool.tsx        # Generic reusable panel for single-prompt tools
    ├── ui.tsx                # Shared primitives: Panel, PrimaryButton, ResultCard, etc.
    └── toast.tsx             # Toast notification system (context + provider)
```

### Tool Routing
`App.tsx` holds a static `TOOLS` array. Each tool has an `id`, `group`, and a `render()` function. The sidebar renders groups (`Apply`, `Prepare`, `Grow`) and clicking a tool swaps the main panel via `activeId` state — no router needed.

### Shared State
`SharedProvider` (in `shared.tsx`) holds cross-tool state (e.g. a job description typed in one tool pre-fills another). Persisted to `localStorage`.

---

## Setup

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Ollama](https://ollama.com/) with `gemma4:26b` and `nomic-embed-text` pulled
- Python 3.11+
- Node.js 20+

```bash
ollama pull gemma4:26b
ollama pull nomic-embed-text
```

### 1. Database

```bash
cd ~/Desktop/Personal/JobAssistant
docker compose up -d
```

Postgres will be available at `localhost:5434`. The `jobassistant` user and database are created automatically by Docker on first run.

### 2. Backend

```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# .env is pre-configured for the Docker setup — no changes needed by default

# Start the API server
uvicorn main:app --reload
```

Backend runs at `http://localhost:8000`. The `resumes` table is created automatically on first startup.

### 3. Frontend

```bash
cd frontend

npm install
npm run dev
```

Frontend runs at `http://localhost:5173` and proxies all `/api/*` requests to the backend.

### 4. Resume

Upload your resume (`.pdf` or `.docx`) via the **Upload Resume** button in the app header. It is extracted, stored in Postgres, and reused across all tools automatically.

### 5. Career Advisor Knowledge Base (optional)

To give the Career Advisor grounded market context, add `.txt` or `.md` files to `scripts/knowledge/` and run the ingestion script:

```bash
cd backend
python ../scripts/ingest.py
```

---

## Running Everything

| Terminal | Command |
|---|---|
| 1 | `docker compose up -d` |
| 2 | `cd backend && source .venv/bin/activate && uvicorn main:app --reload` |
| 3 | `cd frontend && npm run dev` |

Then open `http://localhost:5173`.
