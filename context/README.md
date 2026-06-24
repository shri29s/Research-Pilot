# context/

This folder is the single source of truth for everything about this project —
for humans, for AI assistants, and for future contributors.

---

## When to read what

| You are… | Read |
|---|---|
| Starting a new AI session | `agent/INSTRUCTIONS.md` + `session/CONTEXT.md` |
| Writing or reviewing code | `agent/STANDARDS.md` |
| Committing or pushing | `agent/WORKFLOW.md` |
| Touching structure or stack | `project/ARCHITECTURE.md` |
| Making a non-obvious decision | `project/DECISIONS.md` (for format + history) |
| Integrating an external API | `reference/API_CONTRACTS.md` |
| Unsure what a term means | `reference/GLOSSARY.md` |
| New to the project entirely | `project/MISSION.md` → `project/ARCHITECTURE.md` → `project/DATA_MODEL.md` |

---

## Folder map

```
context/
├── README.md                   ← this file
│
├── project/                    ← stable, rarely changes
│   ├── MISSION.md              ← problem, goals, success criteria
│   ├── ARCHITECTURE.md         ← system design, stack, folder structure
│   ├── DATA_MODEL.md           ← entities, schemas, relationships
│   └── DECISIONS.md            ← ADR log (append-only)
│
├── agent/                      ← AI behavior contract
│   ├── INSTRUCTIONS.md         ← system prompt (always loaded, stays thin)
│   ├── WORKFLOW.md             ← loop, git-allrounder, commit + decision rules
│   └── STANDARDS.md            ← coding standards, naming, error handling
│
├── session/                    ← changes every session
│   ├── CONTEXT.md              ← current state, last built, what's next
│   └── SCRATCHPAD.md           ← temp notes, half-ideas, experiments
│
└── reference/                  ← pull only when needed
    ├── API_CONTRACTS.md        ← external API shapes you integrate with
    ├── STACK_VERSIONS.md       ← pinned versions + why
    └── GLOSSARY.md             ← domain terms, abbreviations, naming conventions
```

---

## Rules for this folder

- `project/` is updated only when the project fundamentally changes.
- `agent/` travels with you across projects — minimal project-specific content.
- `session/CONTEXT.md` is updated at the end of every session, committed with the session's final commit.
- `session/SCRATCHPAD.md` is never committed — add it to `.gitignore`.
- `project/DECISIONS.md` is append-only. Never edit past entries.
- `reference/` files are only loaded into a session when the task requires them.