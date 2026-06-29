# ResearchPilot — Autonomous Academic Synthesis Engine

ResearchPilot is an advanced, multi-agent academic research assistant designed to transform a broad natural language query into a publication-ready, fully cited literature review in minutes. By orchestrating a coordinated team of specialized AI agents, ResearchPilot performs automated academic database searches, embeds abstracts into a semantic vector store, synthesises findings, and subjects drafts to a strict "LLM-as-judge" quality audit before producing the final manuscript.

---

## 1. System Architecture & Multi-Agent Roster

ResearchPilot divides the cognitive burden of research synthesis across six specialized agents, guided by a central supervisor.

```
                  ┌──────────────────────┐
                  │      User Query      │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   Supervisor Agent   │
                  └──────────┬───────────┘
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
┌──────────────────────┐           ┌──────────────────────┐
│   Decomposer Agent   │           │     Writer Agent     │
└──────────┬───────────┘           └──────────▲───────────┘
            │                                 │
            │ (Sub-questions)                 │ (Final Compile)
            ▼                                 │
┌──────────────────────┐                      │
│   Retriever Agent    ├────────┐             │
└──────────────────────┘        ▼             │
                           ┌──────────┐       │
                           │ ChromaDB │       │
                           └────┬─────┘       │
            ┌───────────────────┘             │
            ▼                                 │
┌──────────────────────┐                      │
│  Synthesiser Agent   ├──────────────────────┘
└──────────┬───────────┘
            │ (Draft Synthesis)
            ▼
┌──────────────────────┐
│     Critic Agent     │  ◄── (Audit Loop: Max 2 Iterations)
└──────────────────────┘
```

### The Agent Team
1. **Supervisor Agent (`src/services/supervisor.py`)**
   * **Role:** Central orchestrator and state-machine manager.
   * **Responsibility:** Receives the query, initializes `SessionState`, sequentially delegates tasks, manages the critique-revision loop, and compiles execution logs and telemetry metrics.
2. **Decomposer Agent (`src/services/decomposer.py`)**
   * **Role:** Query segmenter.
   * **Responsibility:** Analyzes the user's broad query and breaks it down into 3-4 distinct, targeted academic sub-questions. This keyword-rich segmentation guarantees vastly superior academic search results.
3. **Retriever Agent (`src/services/retriever.py`)**
   * **Role:** Multi-database academic crawler.
   * **Responsibility:** Queries the Semantic Scholar and ArXiv databases for each sub-question, deduplicates results, computes embeddings using `text-embedding-3-small`, and writes them to a local ChromaDB collection.
4. **Synthesiser Agent (`src/services/synthesiser.py`)**
   * **Role:** Literature surveyor.
   * **Responsibility:** Performs semantic vector search on ChromaDB to retrieve the top 5 most relevant papers for a sub-question. Drafts a cohesive, dense synthesis paragraph with inline citations (`[Author et al., Year]`).
5. **Critic Agent (`src/services/critic.py`)**
   * **Role:** LLM-as-Judge auditor.
   * **Responsibility:** Audits each draft synthesis against the source papers on three metrics (0-10 scale): *Coverage*, *Grounding*, and *Citation Accuracy*. If any score falls below 7/10, it rejects the draft and issues detailed revision notes to the Synthesiser.
6. **Writer Agent (`src/services/writer.py`)**
   * **Role:** Manuscript editor and publisher.
   * **Responsibility:** Compiles individual syntheses, formats clickable biblographical sources with URLs, adds cross-cutting themes, and outputs the final cited Markdown document.

---

## 2. Technical Stack

* **Language & Runtime:** Python 3.12 (managed via `uv`).
* **LLM & Embeddings Backbone:** OpenAI Client wrapper configured for the [AIML API](https://aimlapi.com/) endpoint:
  * **Chat Model:** `gpt-4o-mini`
  * **Embedding Model:** `text-embedding-3-small` (1536 dimensions)
* **Vector Store:** ChromaDB (persisted locally under `chroma_db/`).
* **Academic Integrations:** Semantic Scholar Academic Graph API + official ArXiv Python client.
* **Backend Web Framework:** FastAPI + Uvicorn with Event Stream (Server-Sent Events) generators.
* **Frontend Design:** Vanilla HTML5, CSS3 (Bento layout, Custom CSS variables, Glassmorphism, animations), Javascript client utilizing `marked.js` and `DOMPurify`.

---

## 3. Getting Started & Installation

### Prerequisites
* Python 3.11 or 3.12.
* [uv](https://github.com/astral-sh/uv) (Extremely fast Python package installer and manager).
* An AIML API key (Get one at [https://aimlapi.com/](https://aimlapi.com/)).

### Installation
1. Clone or navigate to the project directory:
   ```bash
   cd capstone
   ```
2. Configure the environment:
   Copy `.env.example` to `.env` in both the workspace root and the `backend/` folder:
   ```bash
   cp .env.example .env
   cp .env.example backend/.env
   ```
3. Populate `.env` with your AIML API Key:
   ```env
   AIMLABS_API_KEY=your_aiml_api_key_here
   ```

---

## 4. Running the Project

### Option A: Command Line Interface (CLI)
To run a literature compilation directly in your terminal, use the root CLI runner:
```bash
uv run main.py "What are the key approaches to handling multi-hop reasoning in RAG systems?"
```
* **Output:** The compiled literature review will be saved to `literature_review.md` in the workspace root, and detailed traces will be logged under `logs/`.

### Option B: Interactive Web Interface (Recommended)
To run the interactive Awwwards-style Bento dashboard:

1. **Start the FastAPI Backend:**
   Navigate to the backend directory, install web-specific dependencies, and run Uvicorn:
   ```bash
   cd backend
   uv pip install -r requirements.txt
   uv run uvicorn main:app --port 8000
   ```
   * *The backend API will run on [http://127.0.0.1:8000](http://127.0.0.1:8000).*

2. **Start the Static Frontend Server:**
   In a separate terminal tab in the workspace root, run the Python static file server:
   ```bash
   python -m http.server 5500 --directory frontend
   ```
   * *The frontend dashboard will run on [http://127.0.0.1:5500](http://127.0.0.1:5500).*

3. **Explore:**
   Open your browser and navigate to [http://127.0.0.1:5500/index.html](http://127.0.0.1:5500/index.html). Type your research inquiry and click **Begin Synthesis** to watch the agents execute and stream the manuscript in real-time.

---

## 5. Project Directory Structure

```
researchpilot/
├── backend/                  # FastAPI Backend API Server
│   ├── agents/               # Web implementation of agents
│   ├── models/               # Pydantic schemas
│   ├── utils/                # LLM & Academic search utilities
│   ├── main.py               # API entry point & SSE generator
│   └── requirements.txt      # Web backend dependencies
│
├── frontend/                 # Vanilla Web UI Dashboard
│   ├── index.html            # Bento Grid markup
│   ├── style.css             # Glassmorphic lab theme
│   └── app.js                # SSE Event dispatcher & formatter
│
├── src/                      # Core CLI Service Library
│   ├── models/               # Shared Pydantic data schemas
│   ├── services/             # CLI agent logic
│   └── utils/                # Observability & LLM functions
│
├── prompts/                  # Centralized system instruction templates
│   ├── supervisor.txt
│   ├── decomposer.txt
│   ├── retriever.txt
│   ├── synthesiser.txt
│   ├── critic.txt
│   └── writer.txt
│
├── chroma_db/                # Local Chroma database persistence
├── logs/                     # Session structured JSONL traces
├── config.py                 # Central config validator
└── main.py                   # CLI entry point runner
```
