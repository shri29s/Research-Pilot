# DATA_MODEL.md — ResearchPilot

## Core Schemas

### `Paper` (Dataclass / Pydantic)
- `id`: str (Formatted as `arxiv_{id}` or `semantic_scholar_{id}`)
- `title`: str
- `authors`: List[str]
- `year`: int
- `abstract`: str
- `source`: str ("arxiv" | "semantic_scholar")
- `citation_count`: int
- `external_url`: str

### `CritiqueReport` (Dataclass / Pydantic)
- `coverage`: int (0-10)
- `grounding`: int (0-10)
- `citations`: int (0-10)
- `revision_notes`: str

### `SessionState` (Orchestrator Working Memory)
- `query`: str
- `sub_questions`: List[str]
- `retrieved_papers`: Dict[str, List[Paper]]
- `synthesis_drafts`: Dict[str, str]
- `critiques`: Dict[str, CritiqueReport]
- `final_report`: str

## Storage Schema (ChromaDB Collection: `research_papers`)
- **Document Content**: Abstract text
- **Metadata Fields**:
  - `title` (str)
  - `authors` (List[str] as JSON-serialized string)
  - `year` (int)
  - `source` (str)
  - `citation_count` (int)
  - `external_url` (str)
