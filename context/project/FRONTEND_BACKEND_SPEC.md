# ResearchPilot — Frontend & Backend Plan
**Agents already implemented. This covers only: HTML/CSS/JS frontend + FastAPI backend wiring + deployment.**

---

## 1. Project Structure

```
researchpilot/
├── frontend/                  # → Vercel
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── backend/                   # → Cloud Run
│   ├── main.py                # FastAPI app, SSE endpoint, imports your agents
│   ├── models.py              # QueryRequest pydantic model
│   ├── requirements.txt
│   └── Dockerfile
```

Your existing agents folder drops into `backend/` as-is. `main.py` just imports and calls them.

---

## 2. Backend — `main.py`

### What it does
- Accepts `POST /run-research` with `{ "query": string }`
- Calls your Supervisor agent
- Streams newline-delimited JSON events back to the frontend
- Has CORS configured for your Vercel domain

### Streaming protocol (the contract between backend and frontend)

Every event is one JSON object per line (`\n` terminated):

```
{"type": "agent_start", "agent": "supervisor"}
{"type": "agent_done",  "agent": "supervisor",   "elapsed_ms": 18}
{"type": "agent_start", "agent": "decomposer"}
{"type": "agent_done",  "agent": "decomposer",   "elapsed_ms": 1823}
{"type": "agent_start", "agent": "retriever"}
{"type": "agent_done",  "agent": "retriever",    "elapsed_ms": 4201}
{"type": "agent_start", "agent": "synthesiser"}
{"type": "agent_done",  "agent": "synthesiser",  "elapsed_ms": 6344}
{"type": "agent_start", "agent": "critic"}
{"type": "agent_done",  "agent": "critic",       "elapsed_ms": 2891}
{"type": "agent_start", "agent": "writer"}
{"type": "token",       "content": "# Literature Review...\n"}
{"type": "token",       "content": "## Sub-question 1..."}
{"type": "agent_done",  "agent": "writer",       "elapsed_ms": 8102}
{"type": "done"}
```

Token events come only from the Writer agent (Gemini streaming). All other agents emit only `agent_start` and `agent_done`.

If anything throws: `{"type": "error", "agent": "retriever", "message": "Rate limited by Semantic Scholar"}`.

### How your Supervisor needs to yield these events

Your Supervisor should be an **async generator** that yields event dicts. If it currently returns a final result rather than yielding, you need to refactor it to yield events as it goes — this is the only change required to your agent code.

```python
# supervisor.py — refactor to async generator
async def run(query: str):
    yield {"type": "agent_start", "agent": "supervisor"}
    state = SessionState(query=query)
    yield {"type": "agent_done", "agent": "supervisor", "elapsed_ms": ...}

    yield {"type": "agent_start", "agent": "decomposer"}
    state.sub_questions = await decomposer.run(query)
    yield {"type": "agent_done", "agent": "decomposer", "elapsed_ms": ...}

    # ... same pattern for retriever, synthesiser, critic ...

    yield {"type": "agent_start", "agent": "writer"}
    async for token in writer.stream(state):      # writer must stream tokens
        yield {"type": "token", "content": token}
    yield {"type": "agent_done", "agent": "writer", "elapsed_ms": ...}

    yield {"type": "done"}
```

If your Writer currently returns the full string rather than streaming, wrap it:
```python
# quick non-streaming fallback for the writer
full_output = writer.run(state)
for chunk in [full_output[i:i+20] for i in range(0, len(full_output), 20)]:
    yield {"type": "token", "content": chunk}
```
This gives the appearance of streaming even if Gemini isn't streaming token-by-token. Fine for a demo.

### `main.py` structure

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json, os

from agents.supervisor import supervisor   # your existing supervisor

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("ALLOWED_ORIGIN", "*")],
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)

class QueryRequest(BaseModel):
    query: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/run-research")
async def run_research(body: QueryRequest):
    async def event_stream():
        try:
            async for event in supervisor.run(body.query):
                yield json.dumps(event) + "\n"
        except Exception as e:
            yield json.dumps({"type": "error", "agent": "supervisor", "message": str(e)}) + "\n"
    return StreamingResponse(event_stream(), media_type="application/x-ndjson")
```

That's the entire backend. ~30 lines. Everything else is your existing agents.

### `requirements.txt`

Add to whatever you already have:
```
fastapi
uvicorn[standard]
```

### `Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8080
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

## 3. Visual Design System

### Concept
**"Deep research lab"** — dark, precise, ink-toned. The signature element is a **live agent trace timeline** on the left: a vertical line connecting 6 agent nodes, filling amber from top to bottom as agents complete. This makes the multi-agent pipeline *visible* in real time, which is itself the demo.

Not the generic dark + acid-green look. Palette is desaturated ink tones with a single warm amber accent — like pencil annotations on dark archival paper.

### Colour Palette
```css
--ink:            #0D0D0F;   /* page background */
--surface:        #141418;   /* card / panel backgrounds */
--surface-raised: #1C1C22;   /* textarea, code blocks */
--border:         #2A2A35;   /* dividers, input borders */
--text-primary:   #E8E6E0;   /* body text */
--text-secondary: #7A7870;   /* labels, captions, placeholders */
--amber:          #C9933A;   /* accent — active dot, button, citation links */
--amber-dim:      #6B4D1A;   /* inactive dots, hover states */
```

### Typography
- **`DM Serif Display`** (Google Fonts) — wordmark only. One serif moment. Used nowhere else.
- **`Inter`** (Google Fonts, variable) — all UI text, labels, agent status, output body.
- **`JetBrains Mono`** (Google Fonts) — inline code in Markdown output, elapsed time in trace.

```css
/* type scale */
--font-display: 'DM Serif Display', serif;
--font-body:    'Inter', sans-serif;
--font-mono:    'JetBrains Mono', monospace;

wordmark:     var(--font-display), 2.4rem, weight 400
h1 (report):  var(--font-body),    1.5rem, weight 600
h2 (section): var(--font-body),    1.15rem, weight 600
body:         var(--font-body),    0.95rem, weight 400, line-height 1.75
label:        var(--font-body),    0.75rem, weight 500, letter-spacing 0.08em, uppercase
mono:         var(--font-mono),    0.85rem
```

### Layout — Two Phases

**Phase 1 — Input view:**
```
┌──────────────────────────────────────────────┐
│  ResearchPilot          [wordmark, top-left] │
│                                              │
│         Ask a research question.             │
│   ┌──────────────────────────────────────┐   │
│   │  [textarea, 4 rows]                  │   │
│   └──────────────────────────────────────┘   │
│                         [ Synthesise → ]     │
│                                              │
│   [example chip]  [example chip]             │
└──────────────────────────────────────────────┘
```

**Phase 2 — Results view** (slides in on submit):
```
┌────────────────────────────────────────────────────┐
│  ResearchPilot                      [New query]    │
├──────────────┬─────────────────────────────────────┤
│ Agent trace  │  Output panel                       │
│              │                                     │
│ ●─Supervisor │  [Markdown streams here,            │
│ │            │   re-rendered on every token]       │
│ ●─Decomposer │                                     │
│ │            │                                     │
│ ○─Retriever  │                                     │
│ │            │                                     │
│ ○─Synthesiser│                                     │
│ │            │  ─────────────────────────────────  │
│ ○─Critic     │  [ ↓ Download .md ]                 │
│ │            │                                     │
│ ○─Writer     │                                     │
│              │                                     │
│  Total: 0.0s │                                     │
└──────────────┴─────────────────────────────────────┘
```

Left trace panel: fixed 220px. Right output panel: fills remaining space. On mobile (< 768px): trace collapses to a horizontal progress strip at top, output fills full width.

---

## 4. Frontend — `index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ResearchPilot</title>

  <!-- Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Inter:wght@400;500;600&family=JetBrains+Mono&display=swap" rel="stylesheet">

  <!-- marked.js — Markdown renderer -->
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <!-- DOMPurify — sanitise marked output before innerHTML -->
  <script src="https://cdn.jsdelivr.net/npm/dompurify/dist/purify.min.js"></script>

  <link rel="stylesheet" href="style.css">
</head>
<body>

  <header>
    <span class="wordmark">ResearchPilot</span>
    <button id="new-query-btn" hidden>New query</button>
  </header>

  <main>

    <!-- PHASE 1: input -->
    <section id="input-panel">
      <p class="hero-label">Ask a research question.</p>
      <textarea id="query-input"
        placeholder="e.g. What are the key approaches to multi-hop reasoning in RAG systems?"
        rows="4"></textarea>
      <div class="input-actions">
        <button id="submit-btn" disabled>Synthesise →</button>
      </div>
      <div id="example-chips">
        <button class="chip" data-query="What are the state-of-the-art approaches to retrieval-augmented generation?">RAG approaches</button>
        <button class="chip" data-query="How do vision transformers compare to CNNs for medical image classification?">Vision transformers vs CNNs</button>
        <button class="chip" data-query="What techniques improve multi-hop reasoning in large language models?">Multi-hop reasoning in LLMs</button>
      </div>
    </section>

    <!-- PHASE 2: results (hidden until submit) -->
    <section id="results-panel" hidden>

      <aside id="agent-trace">
        <div class="trace-line"></div>
        <!-- agent nodes — JS renders these, or hardcode with IDs -->
        <div class="agent-node" id="node-supervisor">
          <div class="dot" id="dot-supervisor"></div>
          <div class="agent-info">
            <span class="agent-name">Supervisor</span>
            <span class="agent-time" id="time-supervisor">—</span>
          </div>
        </div>
        <div class="agent-node" id="node-decomposer">
          <div class="dot" id="dot-decomposer"></div>
          <div class="agent-info">
            <span class="agent-name">Decomposer</span>
            <span class="agent-time" id="time-decomposer">—</span>
          </div>
        </div>
        <div class="agent-node" id="node-retriever">
          <div class="dot" id="dot-retriever"></div>
          <div class="agent-info">
            <span class="agent-name">Retriever</span>
            <span class="agent-time" id="time-retriever">—</span>
          </div>
        </div>
        <div class="agent-node" id="node-synthesiser">
          <div class="dot" id="dot-synthesiser"></div>
          <div class="agent-info">
            <span class="agent-name">Synthesiser</span>
            <span class="agent-time" id="time-synthesiser">—</span>
          </div>
        </div>
        <div class="agent-node" id="node-critic">
          <div class="dot" id="dot-critic"></div>
          <div class="agent-info">
            <span class="agent-name">Critic</span>
            <span class="agent-time" id="time-critic">—</span>
          </div>
        </div>
        <div class="agent-node" id="node-writer">
          <div class="dot" id="dot-writer"></div>
          <div class="agent-info">
            <span class="agent-name">Writer</span>
            <span class="agent-time" id="time-writer">—</span>
          </div>
        </div>
        <div class="trace-total">Total: <span id="total-time">0.0s</span></div>
      </aside>

      <article id="output-panel">
        <div id="output-content"></div>
        <footer id="output-footer" hidden>
          <button id="download-btn">↓ Download .md</button>
        </footer>
      </article>

    </section>
  </main>

  <script src="app.js"></script>
</body>
</html>
```

---

## 5. Frontend — `style.css`

Organised in this order. Write them in this sequence to avoid specificity collisions:

### Section order
1. `@import` for fonts (or use `<link>` in HTML — prefer `<link>` for performance)
2. `:root` — all CSS custom properties
3. Reset — `*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }`
4. `html, body` — background, font, color, min-height
5. `header` — flex row, space-between, padding
6. `.wordmark` — DM Serif Display, font size
7. `#new-query-btn` — small ghost button, amber border, shown only in results phase
8. `#input-panel` — centered column layout, max-width 680px, margin auto
9. `.hero-label` — large label above textarea
10. `#query-input` — full width, dark background, amber bottom-border on focus (not full glow — just bottom edge: `border-bottom: 2px solid var(--amber)`)
11. `#submit-btn` — amber background, ink text, **zero border-radius** (sharp corners — the one deliberate aesthetic contrast), disabled state is dimmed
12. `.chip` — small pill buttons, `--border` border, hover fills `--surface-raised`
13. `#results-panel` — CSS grid: `grid-template-columns: 220px 1fr`, full viewport height
14. `#agent-trace` — left panel, relative positioning for the vertical line
15. `.trace-line` — pseudo-element `::before` on `#agent-trace`, absolute positioned vertical line (2px wide, full height), base color `--border`. CSS variable `--fill-pct` controls a second pseudo-element or a `linear-gradient` that fills amber from top
16. `.agent-node` — flex row, dot + info, 48px tall
17. `.dot` — 10px circle, default `--border` color, transitions on all state changes
18. `.dot.idle` — ring only: `background: transparent; border: 2px solid var(--amber-dim)`
19. `.dot.active` — filled amber + CSS pulse animation
20. `.dot.done` — solid amber, no animation. Use `content: "✓"` via `::after` pseudo or just filled circle
21. `.dot.error` — red (`#C0392B`)
22. `@keyframes pulse` — `scale(1) → scale(1.4) → scale(1)`, `opacity: 1 → 0.5 → 1`, 1.2s infinite
23. `.agent-name` — Inter, 0.85rem, `--text-primary`
24. `.agent-time` — JetBrains Mono, 0.75rem, `--text-secondary`
25. `.trace-total` — bottom of trace panel, mono font, total elapsed
26. `#output-panel` — scrollable, padding
27. `#output-content` — max-width 72ch, line-height 1.75
28. Markdown prose styles (critical — see below)
29. `#output-footer` — sticky bottom of output panel
30. `#download-btn` — ghost button, amber border
31. `@media (max-width: 768px)` — trace becomes horizontal bar, output fills full width
32. `@media (prefers-reduced-motion: reduce)` — remove pulse animation

### Markdown prose styles (most important for output quality)

```css
#output-content h1 {
  font-size: 1.5rem; font-weight: 600;
  margin-top: 2rem; margin-bottom: 0.75rem;
  color: var(--text-primary);
}
#output-content h2 {
  font-size: 1.15rem; font-weight: 600;
  margin-top: 1.75rem; margin-bottom: 0.5rem;
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.3rem;
}
#output-content h3 {
  font-size: 1rem; font-weight: 600;
  margin-top: 1.25rem; margin-bottom: 0.35rem;
}
#output-content p  { margin-bottom: 1rem; }
#output-content ul, #output-content ol { padding-left: 1.5rem; margin-bottom: 1rem; }
#output-content li { margin-bottom: 0.35rem; }
#output-content a  {
  color: var(--amber);
  text-decoration: underline;
  text-underline-offset: 3px;
  text-decoration-thickness: 1px;
}
#output-content a:hover { text-decoration-thickness: 2px; }
#output-content code {
  font-family: var(--font-mono);
  font-size: 0.85em;
  background: var(--surface-raised);
  padding: 0.1em 0.35em;
  border-radius: 3px;
}
#output-content pre {
  background: var(--surface-raised);
  padding: 1rem; border-radius: 6px;
  overflow-x: auto; margin-bottom: 1rem;
}
#output-content pre code { background: none; padding: 0; }
#output-content blockquote {
  border-left: 3px solid var(--amber-dim);
  padding-left: 1rem;
  color: var(--text-secondary);
  margin-bottom: 1rem;
}
#output-content strong { font-weight: 600; color: var(--text-primary); }
```

---

## 6. Frontend — `app.js`

### Constants
```js
const BACKEND_URL = window.location.hostname === "localhost"
  ? "http://localhost:8000/run-research"
  : "https://your-cloud-run-url/run-research";   // replace after Cloud Run deploy

const AGENTS = ["supervisor", "decomposer", "retriever", "synthesiser", "critic", "writer"];
```

### Marked.js setup
Configure once at top of file, before any rendering:
```js
const renderer = new marked.Renderer();
// Force all links to open in new tab
const _link = renderer.link.bind(renderer);
renderer.link = (href, title, text) =>
  `<a href="${href}" target="_blank" rel="noopener noreferrer">${text}</a>`;
marked.setOptions({ renderer, gfm: true, breaks: true });
```

### State variables
```js
let markdownBuffer  = "";     // accumulates full Markdown as tokens arrive
let sessionStart    = null;   // Date.now() when submit clicked
let agentTimers     = {};     // agentId → { startMs, intervalId }
let totalTimerInterval = null;
```

### DOM references (grab once at top)
```js
const queryInput    = document.getElementById("query-input");
const submitBtn     = document.getElementById("submit-btn");
const newQueryBtn   = document.getElementById("new-query-btn");
const inputPanel    = document.getElementById("input-panel");
const resultsPanel  = document.getElementById("results-panel");
const outputContent = document.getElementById("output-content");
const outputFooter  = document.getElementById("output-footer");
const downloadBtn   = document.getElementById("download-btn");
const totalTimeEl   = document.getElementById("total-time");
```

### Phase transition functions
```js
function showInputPhase() {
  inputPanel.hidden   = false;
  resultsPanel.hidden = true;
  newQueryBtn.hidden  = true;
  submitBtn.disabled  = queryInput.value.trim() === "";
  resetTrace();
}

function showResultsPhase() {
  inputPanel.hidden   = true;
  resultsPanel.hidden = false;
  newQueryBtn.hidden  = false;
  outputContent.innerHTML = "";
  outputFooter.hidden = true;
  markdownBuffer = "";
  sessionStart   = Date.now();
  startTotalTimer();
}
```

### Agent trace functions
```js
function setDotState(agentId, state) {
  // state: "idle" | "active" | "done" | "error"
  const dot = document.getElementById(`dot-${agentId}`);
  dot.className = `dot ${state}`;
}

function startAgentTimer(agentId) {
  const startMs = Date.now();
  const el = document.getElementById(`time-${agentId}`);
  const intervalId = setInterval(() => {
    el.textContent = ((Date.now() - startMs) / 1000).toFixed(1) + "s";
  }, 100);
  agentTimers[agentId] = { startMs, intervalId };
}

function stopAgentTimer(agentId, elapsedMs) {
  if (agentTimers[agentId]) {
    clearInterval(agentTimers[agentId].intervalId);
  }
  const el = document.getElementById(`time-${agentId}`);
  el.textContent = (elapsedMs / 1000).toFixed(1) + "s";
}

function updateTraceLine() {
  const doneCount = AGENTS.filter(a =>
    document.getElementById(`dot-${a}`).classList.contains("done")
  ).length;
  const pct = (doneCount / AGENTS.length) * 100;
  document.getElementById("agent-trace").style.setProperty("--fill-pct", `${pct}%`);
}

function resetTrace() {
  AGENTS.forEach(a => {
    setDotState(a, "idle");
    document.getElementById(`time-${a}`).textContent = "—";
    if (agentTimers[a]) clearInterval(agentTimers[a].intervalId);
  });
  agentTimers = {};
  if (totalTimerInterval) clearInterval(totalTimerInterval);
  totalTimeEl.textContent = "0.0s";
  document.getElementById("agent-trace").style.setProperty("--fill-pct", "0%");
}

function startTotalTimer() {
  totalTimerInterval = setInterval(() => {
    totalTimeEl.textContent = ((Date.now() - sessionStart) / 1000).toFixed(1) + "s";
  }, 100);
}
```

### Event handler (dispatches stream events to UI)
```js
function handleEvent(event) {
  switch (event.type) {

    case "agent_start":
      setDotState(event.agent, "active");
      startAgentTimer(event.agent);
      break;

    case "agent_done":
      setDotState(event.agent, "done");
      stopAgentTimer(event.agent, event.elapsed_ms);
      updateTraceLine();
      break;

    case "agent_error":
      setDotState(event.agent, "error");
      stopAgentTimer(event.agent, 0);
      showError(event.agent, event.message);
      break;

    case "token":
      markdownBuffer += event.content;
      outputContent.innerHTML = DOMPurify.sanitize(marked.parse(markdownBuffer));
      // auto-scroll to bottom while streaming
      outputContent.scrollTop = outputContent.scrollHeight;
      break;

    case "error":
      showError(event.agent || "system", event.message);
      break;

    case "done":
      clearInterval(totalTimerInterval);
      outputFooter.hidden = false;
      break;
  }
}

function showError(agent, message) {
  // insert an error banner inside output-content, don't wipe existing content
  const banner = document.createElement("div");
  banner.className = "error-banner";
  banner.textContent = `Error in ${agent}: ${message}`;
  outputContent.appendChild(banner);
}
```

### Stream fetch function
```js
async function streamResearch(query) {
  submitBtn.disabled = true;

  let response;
  try {
    response = await fetch(BACKEND_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
  } catch (err) {
    showError("network", "Could not reach the backend. Is it running?");
    submitBtn.disabled = false;
    return;
  }

  if (!response.ok) {
    showError("backend", `Server returned ${response.status}`);
    submitBtn.disabled = false;
    return;
  }

  const reader  = response.body.getReader();
  const decoder = new TextDecoder();
  let lineBuffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      lineBuffer += decoder.decode(value, { stream: true });
      const lines = lineBuffer.split("\n");
      lineBuffer  = lines.pop();           // keep incomplete last line

      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          handleEvent(JSON.parse(line));
        } catch {
          console.warn("Non-JSON line from stream:", line);
        }
      }
    }
  } catch (err) {
    showError("stream", "Connection dropped mid-stream.");
  }

  submitBtn.disabled = false;
}
```

### Download function
```js
function downloadMarkdown() {
  const blob = new Blob([markdownBuffer], { type: "text/markdown" });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href     = url;
  a.download = "research-synthesis.md";
  a.click();
  URL.revokeObjectURL(url);
}
```

### Event listeners (wired at bottom of file)
```js
// enable submit only when textarea has content
queryInput.addEventListener("input", () => {
  submitBtn.disabled = queryInput.value.trim() === "";
});

// submit on button click
submitBtn.addEventListener("click", () => {
  const query = queryInput.value.trim();
  if (!query) return;
  showResultsPhase();
  streamResearch(query);
});

// submit on Ctrl+Enter / Cmd+Enter in textarea
queryInput.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
    submitBtn.click();
  }
});

// example chips populate textarea
document.querySelectorAll(".chip").forEach(chip => {
  chip.addEventListener("click", () => {
    queryInput.value = chip.dataset.query;
    submitBtn.disabled = false;
    queryInput.focus();
  });
});

// new query resets everything
newQueryBtn.addEventListener("click", showInputPhase);

// download button
downloadBtn.addEventListener("click", downloadMarkdown);

// init
showInputPhase();
```

---

## 7. Deployment

### Backend → Cloud Run

```bash
cd backend

gcloud run deploy researchpilot-backend \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "GEMINI_API_KEY=your_key,ALLOWED_ORIGIN=https://your-app.vercel.app" \
  --memory 1Gi \
  --timeout 300
```

Critical flags:
- `--timeout 300` — default is 60s; synthesis takes longer and will be silently cut off without this
- `--allow-unauthenticated` — required for browser fetch calls
- `--memory 1Gi` — ChromaDB + Gemini client needs headroom; 512MB default may OOM

After deploy, copy the service URL (e.g. `https://researchpilot-backend-xxxx-uc.a.run.app`) and set it as `BACKEND_URL` in `app.js`.

### Frontend → Vercel

```bash
cd frontend
# push to GitHub, connect repo to Vercel
# root directory: frontend/
# no build command (static files)
# no environment variables needed
```

After Vercel deploy, copy your Vercel URL and redeploy Cloud Run with updated `ALLOWED_ORIGIN`.

### Local development
```bash
# backend
cd backend
uvicorn main:app --reload --port 8000

# frontend — open index.html via Live Server (VS Code) or:
python -m http.server 5500 --directory frontend
# BACKEND_URL auto-switches to localhost:8000 via the hostname check in app.js
```

Test streaming end-to-end with curl before touching the frontend:
```bash
curl -X POST http://localhost:8000/run-research \
  -H "Content-Type: application/json" \
  -d '{"query": "test RAG approaches"}' \
  --no-buffer
```
You should see JSON lines appearing one by one. If you see them all at once at the end, your Supervisor isn't yielding — it's returning a collected result. Fix that before building the frontend.

---

## 8. The Only Agent Change Required

If your Supervisor currently looks like this:
```python
async def run(query):
    # ... runs all agents ...
    return final_markdown_string   # ← returns, doesn't yield
```

Refactor it to yield events as shown in Section 2. This is the **only** change needed to your existing agent code. The individual agent implementations (decomposer, retriever, synthesiser, critic, writer) don't need to change — only the Supervisor needs to become a generator that emits stream events.

---

## 9. Edge Cases to Handle

| Case | Where handled |
|---|---|
| Empty query submitted | `submitBtn` disabled when textarea is empty |
| Cold start delay (3–8s before first event) | "Connecting..." shown in output panel until first event arrives — add this as initial `outputContent.innerHTML` before calling `streamResearch()` |
| Network drops mid-stream | Caught in `streamResearch` try/catch, shows error banner |
| Backend 4xx / 5xx | Checked after `fetch`, shows error banner |
| Citation links in output | Handled by marked.js renderer override — all `<a>` tags get `target="_blank"` |
| Very long output (auto-scroll) | `outputContent.scrollTop = outputContent.scrollHeight` on every token event |
| Mobile viewport | CSS breakpoint at 768px, trace → horizontal bar |
| Reduced motion preference | `@media (prefers-reduced-motion: reduce)` disables pulse animation |