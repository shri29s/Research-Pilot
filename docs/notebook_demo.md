# Running ResearchPilot on Kaggle (Notebook Integration)

This document provides copy-pasteable cells to run **ResearchPilot** directly inside a Kaggle Notebook or Google Colab.

---

### Cell 1: Clone and Install Dependencies
Install all required libraries for academic queries, vector indexing, and the Gemini API.

```python
# 1. Install dependencies
!pip install -q google-generativeai chromadb arxiv requests pydantic python-dotenv

# 2. Verify installation
import chromadb
import arxiv
import google.generativeai as genai
print("ChromaDB version:", chromadb.__version__)
print("ArXiv version:", arxiv.__version__)
```

---

### Cell 2: Configure API Key and Environment Settings
In Kaggle, you should store your API key securely in **Kaggle User Secrets** (Add-ons -> Secrets) with the label `GEMINI_API_KEY`.

```python
import os
from kaggle_secrets import UserSecretsClient

try:
    # Load secret key from Kaggle Secrets
    user_secrets = UserSecretsClient()
    gemini_key = user_secrets.get_secret("GEMINI_API_KEY")
    os.environ["GEMINI_API_KEY"] = gemini_key
    print("Successfully loaded GEMINI_API_KEY from Kaggle Secrets.")
except Exception as e:
    # Fallback to manual environment input if running locally or outside Kaggle
    print("Kaggle Secrets not found. Please enter key manually below:")
    import getpass
    gemini_key = getpass.getpass("Enter GEMINI_API_KEY: ")
    os.environ["GEMINI_API_KEY"] = gemini_key

# Set optional environment configurations
os.environ["CHROMA_DB_PATH"] = "chroma_db/"
os.environ["MAX_CRITIQUE_LOOPS"] = "2"
os.environ["LOG_LEVEL"] = "INFO"
os.environ["SEMANTIC_SCHOLAR_LIMIT"] = "5"
os.environ["ARXIV_LIMIT"] = "5"
```

---

### Cell 3: Orchestrate literature review and render output
Initialize the `SupervisorAgent` to run the literature review loop and display the output directly as formatted Markdown inside the notebook.

```python
from IPython.display import display, Markdown
from src.services.supervisor import SupervisorAgent

# 1. Define query
query = "What are the key approaches to handling multi-hop reasoning in RAG systems?"

# 2. Run the supervisor orchestrator
supervisor = SupervisorAgent()
print(f"Orchestrating agents for query: '{query}'...")
report, trace_summary = supervisor.run(query)

# 3. Print telemetry metrics
print("\n=== Execution Telemetry ===")
metrics = trace_summary.get("metrics", {})
print(f"Total latency: {metrics.get('total_latency_ms', 0) / 1000:.2f} seconds")
print(f"Papers retrieved & cached: {metrics.get('total_papers_retrieved', 0)}")

# 4. Display the compiled review report
display(Markdown("## Output Literature Review"))
display(Markdown(report))
```
