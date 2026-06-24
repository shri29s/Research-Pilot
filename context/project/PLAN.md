# PLAN.md — ResearchPilot Implementation Plan

This checklist outlines the phased implementation strategy for the ResearchPilot multi-agent academic assistant. We will tackle this incrementally, verifying each task before moving forward.

---

## Phase 1: Environment & Setup
- [x] **Task 1.1**: Write [requirements.txt](file:///C:/Home/Events/5DayAiAgents/capstone/requirements.txt) with dependencies (google-generativeai, chromadb, arxiv, requests, pydantic, python-dotenv).
- [x] **Task 1.2**: Initialize Git repository (`git init`) and add [.gitignore](file:///C:/Home/Events/5DayAiAgents/capstone/.gitignore) entries.
- [x] **Task 1.3**: Create [.env.example](file:///C:/Home/Events/5DayAiAgents/capstone/.env.example) and instruct user to copy it to `.env` with their `GEMINI_API_KEY`.
- [x] **Task 1.4**: Write `config.py` to validate and load the environment configurations.

## Phase 2: Data Models & Academic Search
- [x] **Task 2.1**: Implement core Pydantic data schemas (`Paper`, `CritiqueReport`, `SessionState`) in `src/models/schemas.py`.
- [x] **Task 2.2**: Implement Semantic Scholar and ArXiv search utility APIs in `src/utils/academic_search.py`.
- [x] **Task 2.3**: Set up local ChromaDB vector store utility functions in `src/services/vector_store.py`.

## Phase 3: Core Agents (ADK System Prompts)
- [x] **Task 3.1**: Create prompt templates inside the `prompts/` directory for each agent.
- [x] **Task 3.2**: Implement `DecomposerAgent` (query decomposition logic).
- [x] **Task 3.3**: Implement `RetrieverAgent` (fetching, embedding, and loading to DB).
- [x] **Task 3.4**: Implement `SynthesiserAgent` (semantic querying and drafting).
- [x] **Task 3.5**: Implement `CriticAgent` (LLM-as-judge scoring).
- [x] **Task 3.6**: Implement `WriterAgent` (structured Markdown compiler).

## Phase 4: Orchestration & Observability
- [x] **Task 4.1**: Implement the `SupervisorAgent` state-machine running the critique-iteration loop.
- [x] **Task 4.2**: Set up the dynamic `Tracer` class and logger to output JSON traces.
- [x] **Task 4.3**: Implement `main.py` CLI interface as the entry point.
- [x] **Task 4.4**: Create a sample Kaggle notebook template showing usage.
