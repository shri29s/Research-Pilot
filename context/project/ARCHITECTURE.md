# ResearchPilot — Architecture & Submission Draft
**Kaggle AI Agents Vibe Coding Capstone | Track: Agents for Good**

---

## 1. The Pitch

### Problem
Literature review is the most time-intensive and cognitively expensive part of any research project. A researcher starting a new topic spends 2–4 weeks manually searching databases, skimming abstracts, extracting relevant claims, checking cross-citations, and synthesising findings — before writing a single line of their own work. The result is often incomplete (important papers missed), inconsistent (different standards applied across papers), and unreproducible (the search strategy isn't documented).

For students doing internships (like an NIT Trichy RAG internship), this problem is acute: limited time, steep learning curves, and no institutional access to tools like Elsevier or Clarivate.

### Solution
**ResearchPilot** is a multi-agent research assistant that takes a natural language research query and returns a structured, cited literature synthesis in minutes. It decomposes the query into sub-questions, retrieves relevant papers from open academic APIs, builds a semantic memory of the retrieved knowledge, synthesises findings across papers, and evaluates synthesis quality using an LLM-as-judge agent — all orchestrated by a supervisor agent.

### Value
- Cuts literature review from weeks to minutes for researchers and students
- Fully open-source, built on free academic APIs — no institutional access required
- Produces reproducible, auditable output (search strategy is logged and traceable)
- Demonstrates every key course concept: multi-agent orchestration, tool use, long-term memory, observability, and production-ready evaluation

---

## 2. Architecture

### Agent Roster (6 Agents)

| Agent | Role | Key Tools | Memory Access |
|---|---|---|---|
| **Supervisor** | Query intake, task decomposition, orchestration | None (pure reasoning) | Working memory (session state) |
| **Decomposer** | Breaks query into N sub-questions | LLM reasoning | None |
| **Retriever** | Fetches papers per sub-question | Semantic Scholar API, ArXiv API | Writes to paper store |
| **Synthesiser** | Reads retrieved papers, generates synthesis per sub-question | Vector search over paper store | Reads from paper store |
| **Critic (LLM-as-Judge)** | Evaluates synthesis quality: coverage, accuracy, citation validity | LLM reasoning | Reads synthesis output |
| **Writer** | Assembles final structured report with citations | None | Reads synthesis + critique |

### Orchestration Pattern
```
User Query
    │
    ▼
Supervisor Agent
    ├── → Decomposer Agent → [Sub-question 1, Sub-question 2, ..., Sub-question N]
    │
    ├── For each sub-question (parallel fan-out):
    │       → Retriever Agent → Paper Store (vector DB)
    │       → Synthesiser Agent (reads Paper Store) → Draft synthesis
    │
    ├── → Critic Agent → Quality scores + revision flags
    │       (loops back to Synthesiser if score < threshold)
    │
    └── → Writer Agent → Final structured report (Markdown + citations)
```

### Tool Definitions

**Retriever Agent Tools:**
- `search_semantic_scholar(query: str, limit: int) -> List[Paper]`
  - Calls Semantic Scholar Academic Graph API
  - Returns: title, abstract, authors, year, citationCount, externalIds
- `search_arxiv(query: str, max_results: int) -> List[Paper]`
  - Calls ArXiv API (no key required)
  - Returns: id, title, abstract, authors, published, pdf_url
- `store_paper(paper: Paper, embedding: List[float]) -> str`
  - Embeds abstract using Gemini Embedding API
  - Stores in ChromaDB with metadata
  - Returns: paper_id

**Synthesiser Agent Tools:**
- `retrieve_relevant_papers(sub_question: str, top_k: int) -> List[Paper]`
  - Semantic search over ChromaDB
  - Returns top-k papers ranked by relevance to sub-question
- `get_full_abstract(paper_id: str) -> str`
  - Returns full abstract + metadata for a specific paper

**Critic Agent Tools:**
- `score_synthesis(synthesis: str, papers: List[Paper]) -> CritiqueReport`
  - LLM-as-judge prompt: rates coverage (0-10), factual grounding (0-10), citation accuracy (0-10)
  - Returns structured CritiqueReport with scores and specific revision suggestions

### Memory Design

**Short-term (Session Working Memory):**
- Maintained by Supervisor as a Python dict passed between agents
- Contains: original query, decomposed sub-questions, retrieval status per sub-question, synthesis drafts, critique scores

**Long-term (Persistent Paper Store):**
- ChromaDB collection: `research_papers`
- Schema per document:
  ```
  {
    "id": "semantic_scholar_{id}",
    "embedding": [...],   # 768-dim from Gemini text-embedding-004
    "metadata": {
      "title": str,
      "authors": List[str],
      "year": int,
      "source": "semantic_scholar" | "arxiv",
      "citation_count": int,
      "external_url": str
    },
    "document": str       # abstract text (used for retrieval)
  }
  ```
- Persists across runs — second query on the same topic reuses cached papers

**Episodic Memory (optional stretch goal):**
- Store past queries + generated reports in SQLite
- Supervisor checks episodic memory before decomposing — avoids redundant retrieval on similar queries

### Observability (Day 4 concepts)

**Logging:**
- Every agent action logged with: timestamp, agent_name, tool_called, input_summary, output_summary, duration_ms
- Log format: structured JSON to `logs/session_{timestamp}.jsonl`

**Tracing:**
- Full session trace stored as a directed graph: nodes = agent invocations, edges = data flow
- Trace exportable as JSON for post-hoc debugging
- Implemented via a lightweight `Tracer` class wrapping each agent call

**Metrics tracked:**
- `retrieval_count`: papers fetched per sub-question
- `retrieval_latency_ms`: API call time
- `synthesis_iterations`: how many Critic → Synthesiser loops ran
- `critic_scores`: coverage / grounding / citation scores (per sub-question)
- `total_latency_ms`: end-to-end wall time

**LLM-as-Judge (Critic Agent) Prompt:**
```
You are a rigorous academic reviewer. Given the synthesis below and the source papers,
evaluate on three dimensions (score 0-10 each):

1. Coverage: Does the synthesis address the sub-question fully, using information from all relevant papers?
2. Factual Grounding: Are all claims in the synthesis directly supported by the source papers?
3. Citation Accuracy: Are citations correctly attributed — no hallucinated references?

Sub-question: {sub_question}
Source Papers: {papers_with_abstracts}
Synthesis: {synthesis_draft}

Respond as JSON: {"coverage": int, "grounding": int, "citations": int, "revision_notes": str}
```

### Critique Loop
- If any score < 7 out of 10: Supervisor re-routes to Synthesiser with the Critic's revision notes
- Max 2 revision iterations per sub-question (prevents infinite loops)
- Final synthesis is passed to Writer regardless, with critique scores logged

---

## 3. Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Orchestration | Google ADK (Agent Development Kit) | Required by course; handles agent-to-agent messaging |
| LLM backbone | Gemini 1.5 Flash | Free tier, fast, long context window (needed for multi-paper synthesis) |
| Embeddings | Gemini text-embedding-004 | Same API key, no extra setup |
| Vector store | ChromaDB (local) | Zero infrastructure, persists to disk, Python-native |
| Paper retrieval | Semantic Scholar API + ArXiv API | Both free, no key required for basic use |
| Observability | Custom Tracer class + structured logging | Lightweight, avoids external dependencies |
| Output format | Markdown + JSON | Readable in Kaggle notebook, parseable downstream |
| Deployment (stretch) | Vertex AI Agent Engine | Day 5 concept — deploy supervisor as a scalable endpoint |

---

## 4. Output Format

Final report structure (Markdown):
```markdown
# Literature Review: {original_query}
**Generated by ResearchPilot | {timestamp} | Papers retrieved: N**

---

## Sub-question 1: {sub_question}
{synthesis paragraph with inline citations}

**Sources:**
- [Author et al., Year] Title. Semantic Scholar / ArXiv. [link]
- ...

**Quality score:** Coverage 8/10 | Grounding 9/10 | Citations 10/10

---

## Sub-question 2: ...

---

## Cross-cutting Themes
{Writer agent's synthesis of themes that appeared across multiple sub-questions}

---

## Search Audit Trail
- Query decomposed into N sub-questions
- Total papers retrieved: M (Semantic Scholar: X, ArXiv: Y)
- Total synthesis iterations: K
- Total wall time: T seconds
```

---

## 5. Course Concepts Demonstrated (minimum 3 required)

| Concept | Where demonstrated |
|---|---|
| ✅ Agent tool use | Retriever (Semantic Scholar/ArXiv APIs), Synthesiser (vector search) |
| ✅ Multi-agent orchestration | Supervisor → Decomposer → Retriever → Synthesiser → Critic → Writer |
| ✅ Long-term memory | ChromaDB paper store persisting across sessions |
| ✅ Short-term / working memory | Session state dict maintained by Supervisor |
| ✅ LLM-as-judge evaluation | Critic Agent scoring synthesis quality on 3 dimensions |
| ✅ Observability (logs, traces, metrics) | Custom Tracer + structured JSON logs + per-agent metrics |
| ✅ Agent-to-agent protocol (stretch) | A2A between Supervisor and Critic for revision requests |
| ✅ Production deployment (stretch) | Supervisor deployed to Vertex AI Agent Engine |

---

## 6. Submission Writeup Narrative

### Category 1: The Pitch (30 pts)

**Problem:**
Every researcher spends weeks reading papers before they can write a single sentence of original work. The literature review is the biggest bottleneck in research — and the most repetitive. For students and researchers without expensive institutional tools, it's even worse: manual Semantic Scholar searches, scattered notes, no systematic synthesis.

**Solution:**
ResearchPilot is a multi-agent system that transforms a plain English research query into a structured, cited literature review. It does in minutes what takes a human researcher days — without hallucinating references or missing key papers.

**Value:**
- For researchers: accelerated onboarding to new topics
- For students: levels the playing field (no institutional access needed)
- For reproducibility: every review comes with a full audit trail of what was searched and retrieved

**Why agents, not a single LLM call?**
A single LLM call can't retrieve live papers, can't search multiple databases in parallel, can't loop back for quality improvement, and can't maintain a paper store across sessions. The agentic architecture is not decoration — each agent does something that genuinely cannot be done in a single prompt.

---

### Category 2: The Implementation (70 pts)

**Architecture overview:** Six agents with clearly separated responsibilities. The Supervisor holds working memory as session state; the Retriever writes to a persistent ChromaDB paper store; the Synthesiser reads from it semantically; the Critic runs LLM-as-judge evaluation; the Writer assembles the final output.

**Technical decisions:**
- Chose ChromaDB over Pinecone/Weaviate for zero infrastructure overhead (Kaggle notebook friendly)
- Chose Gemini Flash over Pro for retrieval speed — synthesis quality matters more than per-call capability
- Critique loop capped at 2 iterations — prevents runaway costs while improving output quality
- Semantic Scholar preferred over Google Scholar (proper API, structured metadata, citation counts)

**Evaluation:**
Every synthesis is scored by the Critic on coverage, grounding, and citation accuracy. Scores are logged and displayed in the final report, making quality measurable and transparent — not just "it looks good."

**Code quality:**
- Each agent is a self-contained class with a single `run(input) -> output` interface
- Tools are typed functions with docstrings
- Tracer wraps every agent call transparently — no observability code mixed into agent logic
- Session state is a typed dataclass, not a loose dict

---

## 7. Demo Script (for video submission)

1. **[0:00–0:30]** — Problem statement: "I spent 3 weeks manually reading RAG papers for my NIT Trichy internship. This agent does it in under 3 minutes."
2. **[0:30–1:00]** — Run ResearchPilot on: *"What are the key approaches to handling multi-hop reasoning in RAG systems?"*
3. **[1:00–1:45]** — Show the Supervisor decomposing the query into 4 sub-questions live
4. **[1:45–2:30]** — Show Retriever fetching papers from Semantic Scholar + ArXiv (real API calls)
5. **[2:30–3:00]** — Show Critic agent scoring a synthesis, triggering a revision
6. **[3:00–3:45]** — Show final report with citations and audit trail
7. **[3:45–4:00]** — Show ChromaDB paper store persisting — second query is faster
8. **[4:00–4:30]** — (Optional) Show Vertex AI Agent Engine deployment endpoint

---

## 8. Build Order (Implementation Sequence)

1. `Paper` and `CritiqueReport` dataclasses + `SessionState` dataclass
2. ChromaDB setup + `store_paper` + `retrieve_relevant_papers` tools
3. Semantic Scholar + ArXiv API wrapper functions
4. Individual agents: Decomposer → Retriever → Synthesiser → Critic → Writer
5. Supervisor orchestration loop with critique-revision logic
6. `Tracer` class + structured logger
7. Markdown report assembly
8. Kaggle notebook wrapper (clean cells, output examples)
9. (Stretch) Vertex AI Agent Engine deployment
10. Video recording + writeup polish

---

## 9. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Semantic Scholar API rate limits | Exponential backoff + cache results in ChromaDB |
| LLM hallucinating paper titles | Critic validates citations against retrieved paper list |
| Synthesis too long for context window | Chunk abstracts, summarise per paper before synthesis |
| Critique loop running forever | Hard cap at 2 iterations, log final score regardless |
| Kaggle notebook timeout | Pre-cache paper store, show pre-run outputs in notebook |