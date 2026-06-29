// ==========================================================================
// ResearchPilot Front-End Controller
// ==========================================================================

const BACKEND_URL = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
  ? "http://localhost:8000/run-research"
  : "https://researchpilot-backend-80d4623c-7e9a-43a9-92c0-ccaafab64c5c.a.run.app/run-research"; // Placeholder URL to be replaced on actual Cloud Run deployment

const AGENTS = ["supervisor", "decomposer", "retriever", "synthesiser", "critic", "writer"];

// 1. Marked.js setup with target="_blank" override for citations
try {
  const renderer = {
    link(hrefOrToken, title, text) {
      let href = hrefOrToken;
      let linkText = text;
      if (typeof hrefOrToken === "object" && hrefOrToken !== null) {
        href = hrefOrToken.href;
        linkText = hrefOrToken.text;
      }
      return `<a href="${href || ''}" target="_blank" rel="noopener noreferrer">${linkText || ''}</a>`;
    }
  };
  marked.use({ renderer, gfm: true, breaks: true });
} catch (e) {
  console.warn("Failed to set custom marked.js options, using defaults. Error:", e);
}

// 2. State variables
let markdownBuffer = "";      // accumulates full Markdown as tokens arrive
let sessionStart = null;      // Date.now() when submit clicked
let agentTimers = {};        // agentId -> { startMs, intervalId }
let totalTimerInterval = null;

// 3. DOM references
const queryInput    = document.getElementById("query-input");
const submitBtn     = document.getElementById("submit-btn");
const newQueryBtn   = document.getElementById("new-query-btn");
const inputPanel    = document.getElementById("input-panel");
const resultsPanel  = document.getElementById("results-panel");
const outputContent = document.getElementById("output-content");
const outputPanel   = document.getElementById("output-panel");
const outputFooter  = document.getElementById("output-footer");
const downloadBtn   = document.getElementById("download-btn");
const totalTimeEl   = document.getElementById("total-time");
const activeStateEl = document.getElementById("active-state");

// 4. Phase transition functions
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
  
  // Show initial connecting/connecting state
  outputContent.innerHTML = `<div class="connecting-banner">Connecting to Research Agents</div>`;
  outputFooter.hidden = true;
  markdownBuffer = "";
  sessionStart   = Date.now();
  startTotalTimer();
  if (activeStateEl) activeStateEl.textContent = "INITIALIZING";
}

// 5. Agent trace functions
function setDotState(agentId, state) {
  // state: "idle" | "active" | "done" | "error"
  const dot = document.getElementById(`dot-${agentId}`);
  if (dot) {
    dot.className = `dot ${state}`;
  }
  
  const node = document.getElementById(`node-${agentId}`);
  if (node) {
    if (state === "active") {
      node.classList.add("active-row");
      node.classList.remove("done-row");
    } else if (state === "done") {
      node.classList.remove("active-row");
      node.classList.add("done-row");
    } else {
      node.classList.remove("active-row");
      node.classList.remove("done-row");
    }
  }
}

function startAgentTimer(agentId) {
  // Clear any existing timer first
  if (agentTimers[agentId]) {
    clearInterval(agentTimers[agentId].intervalId);
  }
  
  const startMs = Date.now();
  const el = document.getElementById(`time-${agentId}`);
  const intervalId = setInterval(() => {
    if (el) {
      el.textContent = ((Date.now() - startMs) / 1000).toFixed(1) + "s";
    }
  }, 100);
  agentTimers[agentId] = { startMs, intervalId };
}

function stopAgentTimer(agentId, elapsedMs) {
  if (agentTimers[agentId]) {
    clearInterval(agentTimers[agentId].intervalId);
  }
  const el = document.getElementById(`time-${agentId}`);
  if (el) {
    el.textContent = (elapsedMs / 1000).toFixed(1) + "s";
  }
}

function updateTraceLine() {
  const doneCount = AGENTS.filter(a => {
    const dot = document.getElementById(`dot-${a}`);
    return dot && dot.classList.contains("done");
  }).length;
  
  const pct = (doneCount / AGENTS.length) * 100;
  document.getElementById("agent-trace").style.setProperty("--fill-pct", `${pct}%`);
}

function resetTrace() {
  AGENTS.forEach(a => {
    setDotState(a, "idle");
    const el = document.getElementById(`time-${a}`);
    if (el) el.textContent = "—";
    if (agentTimers[a]) {
      clearInterval(agentTimers[a].intervalId);
    }
  });
  agentTimers = {};
  if (totalTimerInterval) clearInterval(totalTimerInterval);
  totalTimeEl.textContent = "0.0s";
  if (activeStateEl) activeStateEl.textContent = "STANDBY";
  document.getElementById("agent-trace").style.setProperty("--fill-pct", "0%");
}

function startTotalTimer() {
  totalTimerInterval = setInterval(() => {
    totalTimeEl.textContent = ((Date.now() - sessionStart) / 1000).toFixed(1) + "s";
  }, 100);
}

function formatManuscriptOutput(html) {
  // Replace Quality Metrics with premium UI components
  let formatted = html.replace(/<p><em>Quality Metrics: Coverage (\d+)\/10 \| Grounding (\d+)\/10 \| Citations (\d+)\/10<\/em><\/p>/gi, (match, cov, grd, cit) => {
    const cVal = parseInt(cov);
    const gVal = parseInt(grd);
    const ciVal = parseInt(cit);
    const isPassing = cVal >= 7 && gVal >= 7 && ciVal >= 7;
    const statusClass = isPassing ? 'status-pass' : 'status-fail';
    const statusText = isPassing ? 'PASSED AUDIT' : 'FAILED AUDIT';
    
    return `
      <div class="quality-card ${statusClass}">
        <div class="quality-header">
          <span class="quality-title">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right: 4px; vertical-align: middle;">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
            CRITIC QUALITY METRICS
          </span>
          <span class="quality-status">${statusText}</span>
        </div>
        <div class="metrics-grid">
          <div class="metric-item">
            <div class="metric-info">
              <span class="metric-name">Coverage</span>
              <span class="metric-score">${cVal}/10</span>
            </div>
            <div class="metric-bar-bg">
              <div class="metric-bar" style="width: ${cVal * 10}%"></div>
            </div>
          </div>
          <div class="metric-item">
            <div class="metric-info">
              <span class="metric-name">Grounding</span>
              <span class="metric-score">${gVal}/10</span>
            </div>
            <div class="metric-bar-bg">
              <div class="metric-bar" style="width: ${gVal * 10}%"></div>
            </div>
          </div>
          <div class="metric-item">
            <div class="metric-info">
              <span class="metric-name">Citations</span>
              <span class="metric-score">${ciVal}/10</span>
            </div>
            <div class="metric-bar-bg">
              <div class="metric-bar" style="width: ${ciVal * 10}%"></div>
            </div>
          </div>
        </div>
      </div>
    `;
  });

  // Replace Reviewer Notes with a premium alert box
  formatted = formatted.replace(/<p><em>Reviewer Notes: (.*?)<\/em><\/p>/gi, (match, notes) => {
    return `
      <div class="reviewer-notes-card">
        <div class="reviewer-notes-header">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right: 4px; vertical-align: middle;">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
            <line x1="12" y1="9" x2="12" y2="13"></line>
            <line x1="12" y1="17" x2="12.01" y2="17"></line>
          </svg>
          CRITIC REVISION FEEDBACK
        </div>
        <div class="reviewer-notes-text">${notes}</div>
      </div>
    `;
  });

  return formatted;
}

// 6. Event handler (dispatches stream events to UI)
function handleEvent(event) {
  switch (event.type) {

    case "agent_start":
      setDotState(event.agent, "active");
      startAgentTimer(event.agent);
      if (activeStateEl) activeStateEl.textContent = event.agent.toUpperCase();
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
      if (activeStateEl) activeStateEl.textContent = "ERROR";
      break;

    case "clear_buffer":
      markdownBuffer = "";
      outputContent.innerHTML = "";
      break;

    case "token":
      // Remove connecting banner on first token event or replace content
      const banner = outputContent.querySelector(".connecting-banner");
      if (banner) {
        outputContent.innerHTML = "";
      }
      
      markdownBuffer += event.content;
      try {
        const rawHtml = DOMPurify.sanitize(marked.parse(markdownBuffer));
        outputContent.innerHTML = formatManuscriptOutput(rawHtml);
      } catch (err) {
        outputContent.textContent = markdownBuffer; // Fallback
      }
      
      // Auto-scroll the output panel to the bottom during streaming
      if (outputPanel) {
        outputPanel.scrollTop = outputPanel.scrollHeight;
      }
      break;

    case "error":
      showError(event.agent || "system", event.message);
      if (activeStateEl) activeStateEl.textContent = "ERROR";
      break;

    case "done":
      if (totalTimerInterval) clearInterval(totalTimerInterval);
      outputFooter.hidden = false;
      if (activeStateEl) activeStateEl.textContent = "COMPLETED";
      
      // Force scroll to bottom once completed
      setTimeout(() => {
        if (outputPanel) outputPanel.scrollTop = outputPanel.scrollHeight;
      }, 50);
      break;
  }
}

function showError(agent, message) {
  // Remove connecting banner if present
  const banner = outputContent.querySelector(".connecting-banner");
  if (banner) {
    outputContent.innerHTML = "";
  }
  
  const errEl = document.createElement("div");
  errEl.className = "error-banner";
  errEl.textContent = `Error in ${agent}: ${message}`;
  outputContent.appendChild(errEl);
  if (outputPanel) {
    outputPanel.scrollTop = outputPanel.scrollHeight;
  }
}

// 7. Stream fetch function
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
    showError("network", "Could not reach the backend API. Please check if the FastAPI server is running on port 8000.");
    submitBtn.disabled = false;
    if (totalTimerInterval) clearInterval(totalTimerInterval);
    return;
  }

  if (!response.ok) {
    showError("backend", `Server returned status code ${response.status}`);
    submitBtn.disabled = false;
    if (totalTimerInterval) clearInterval(totalTimerInterval);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let lineBuffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      lineBuffer += decoder.decode(value, { stream: true });
      const lines = lineBuffer.split("\n");
      lineBuffer  = lines.pop(); // keep incomplete last line in the buffer

      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          handleEvent(JSON.parse(line));
        } catch (e) {
          console.warn("Could not parse line as JSON:", line);
        }
      }
    }
  } catch (err) {
    showError("stream", "Connection with the backend stream was interrupted.");
  }

  submitBtn.disabled = false;
}

// 8. Download report function
function downloadMarkdown() {
  const blob = new Blob([markdownBuffer], { type: "text/markdown" });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href     = url;
  a.download = "literature-review.md";
  a.click();
  URL.revokeObjectURL(url);
}

// 9. Event listeners wiring
queryInput.addEventListener("input", () => {
  submitBtn.disabled = queryInput.value.trim() === "";
});

submitBtn.addEventListener("click", () => {
  const query = queryInput.value.trim();
  if (!query) return;
  showResultsPhase();
  streamResearch(query);
});

// Support Ctrl+Enter or Cmd+Enter to submit
queryInput.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
    if (queryInput.value.trim() !== "") {
      submitBtn.click();
    }
  }
});

// Example chips populating query input
document.querySelectorAll(".chip").forEach(chip => {
  chip.addEventListener("click", () => {
    queryInput.value = chip.dataset.query;
    submitBtn.disabled = false;
    queryInput.focus();
  });
});

newQueryBtn.addEventListener("click", showInputPhase);
downloadBtn.addEventListener("click", downloadMarkdown);

// Initial initialization
showInputPhase();
