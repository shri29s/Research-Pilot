# ResearchPilot Session Context

## Current Status
- **Goal**: Run the multi-agent literature review compiler for the query: `"What are the key approaches to handling multi-hop reasoning in RAG systems?"`
- **Current State**: The Python runtime, model selection, prompt string formatting, and rate-limiting issues have all been resolved. However, the latest run hit the daily Free Tier limit of 20 requests per day on the provided Gemini API key. The next execution should be run once the quota resets or using an API key with higher limits.

---

## Technical Issues Resolved

### 1. Python 3.14 Compatibility & Virtual Environment
- **Symptoms**: `TypeError: Metaclasses with custom tp_new are not supported` from `protobuf` under Python 3.14.
- **Resolution**:
  - Constrained Python version in [pyproject.toml](file:///C:/Home/Events/5DayAiAgents/capstone/pyproject.toml) to `requires-python = ">=3.11,<3.13"`.
  - Updated [.python-version](file:///C:/Home/Events/5DayAiAgents/capstone/.python-version) to `3.12`.
  - This forces `uv` to automatically download and configure a virtual environment with Python 3.12, avoiding Python 3.14 runtime errors.

### 2. Prompt Formatter KeyError (`'sub_question'` and `'\n  "coverage"'`)
- **Symptoms**: When compiling final reports or reviewing synthesis, agents failed with `KeyError` inside the `.format()` call. This was due to JSON-braces and formatting guide-braces in [prompts/critic.txt](file:///C:/Home/Events/5DayAiAgents/capstone/prompts/critic.txt) and [prompts/writer.txt](file:///C:/Home/Events/5DayAiAgents/capstone/prompts/writer.txt) colliding with Python's string `.format()` logic.
- **Resolution**:
  - Modified [src/services/critic.py](file:///C:/Home/Events/5DayAiAgents/capstone/src/services/critic.py) and [src/services/writer.py](file:///C:/Home/Events/5DayAiAgents/capstone/src/services/writer.py) to use chained `.replace()` calls instead of `.format()` for prompt generation. This is robust to brace usage in templates.

### 3. Model Availability (404 Not Found)
- **Symptoms**: `404 models/gemini-1.5-flash is not found for API version v1beta` when invoking the LLM.
- **Resolution**:
  - Queried available models for the current API key and found that `gemini-1.5-flash` was not supported, but newer models like `gemini-2.0-flash`, `gemini-2.5-flash`, and `models/gemini-embedding-2` are.
  - Updated [src/utils/llm.py](file:///C:/Home/Events/5DayAiAgents/capstone/src/utils/llm.py) to use `"gemini-2.0-flash"`.
  - Updated [src/services/vector_store.py](file:///C:/Home/Events/5DayAiAgents/capstone/src/services/vector_store.py) to use `"models/gemini-embedding-2"`.

### 4. API Rate Limiting (429 Quota Exceeded)
- **Symptoms**: Sequential execution of multi-agent loops easily hits the Gemini Free Tier limit (5 requests per minute, 20 requests per day).
- **Resolution**:
  - Implemented an automatic retry mechanism with **exponential backoff** in `call_gemini` inside [src/utils/llm.py](file:///C:/Home/Events/5DayAiAgents/capstone/src/utils/llm.py) (retrying up to 5 times starting at a 5s delay).

---

## Recommended Next Steps
1. **API Key**: If possible, swap the `GEMINI_API_KEY` in [.env](file:///C:/Home/Events/5DayAiAgents/capstone/.env) with a paid-tier key or one that has a higher daily quota limit.
2. **Alternative Model**: If quota remains an issue, try changing the model name in [src/utils/llm.py](file:///C:/Home/Events/5DayAiAgents/capstone/src/utils/llm.py) to `gemini-2.0-flash-lite` which has much higher free limits.
3. **Execution**: Run the command:
   ```bash
   uv run main.py "What are the key approaches to handling multi-hop reasoning in RAG systems?"
   ```
