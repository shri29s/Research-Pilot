# DECISIONS.md
> Append-only ADR log. Never edit past entries — add a new one that supersedes them.
> One entry per non-obvious decision. Committed alongside the code it governs.

---

## [ADR-001] ChromaDB for Local Vector Storage

**Date:** 2026-06-24
**Status:** decided

**Context:**
The agent needs to query papers semantically inside a Kaggle notebook. Setup should be zero-overhead and highly portable.

**Options considered:**
- Pinecone — requires external API keys, internet traffic, and setup overhead.
- Pgvector — requires running PostgreSQL locally, which is heavy for a notebook environment.
- ChromaDB (local persistence) — zero infrastructure, native python installation, local directories.

**Decision:**
ChromaDB (local persistence) was chosen.

**Consequences:**
Enables easy deployment in Kaggle/Colab notebooks, offline semantic caching, and zero database hosting costs.

---

## [ADR-002] Gemini 1.5 Flash as Core Backbone

**Date:** 2026-06-24
**Status:** decided

**Context:**
The supervisor agent spawns parallel fan-out calls to analyze papers for multiple sub-questions. High rate limits, long context windows, and low latency are critical.

**Options considered:**
- Gemini 1.5 Pro — high reasoning capability, but higher latency and more restrictive free-tier rate limits.
- Claude 3.5 Sonnet — premium intelligence but lacks free-tier scaling and has smaller context windows.
- Gemini 1.5 Flash — fast, has a 1M+ token context window (perfect for multi-paper abstracts), and highly permissive free tier.

**Decision:**
Gemini 1.5 Flash was chosen.

**Consequences:**
Drastically reduces end-to-end execution latency and keeps the capstone project entirely free to run.