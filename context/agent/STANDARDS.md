# STANDARDS.md
> Read this when writing or reviewing any code.

---

## Structure rules
- One responsibility per function, class, and module.
- Routes / CLI handlers are thin: parse → call service → return. Zero logic.
- Business logic lives in `src/services/` or `src/core/` only.
- `main.py` wires things together — zero business logic.
- Config loaded once at startup in `config.py`, injected where needed.
- LLM prompts in `prompts/` as `.txt` or `.md` — never inline strings.

## Naming
- Python: `snake_case` functions/vars, `PascalCase` classes, `UPPER_SNAKE_CASE` constants
- Files: `snake_case.py`
- Names say what a thing *is* or *does* — not how it works internally.

## Configuration
- All env-specific values go in `.env` — API keys, URLs, timeouts, model names, feature flags.
- Never inline these in source files.
- Fail loudly at startup if a required var is missing.

## Error handling
- No bare `except:` or empty `catch {}`.
- External calls (APIs, DB, file I/O) always have try/except with a meaningful message.
- Functions return structured errors for expected failure states — don't raise for those.

## Logging
- Use the project logger, never `print()`.
- Levels: DEBUG (internals), INFO (state changes), WARNING (recoverable), ERROR (failures).
- Log inputs/outputs of critical operations. Never log secrets.

## Testing
- Write the test right after the function — not later.
- Unit tests: mock all external deps.
- Test name describes the scenario: `test_login_fails_on_wrong_password`.
- Tests mirror source structure: `src/services/auth.py` → `tests/unit/test_auth.py`.

## Types
- Type hints on all function signatures.
- Pydantic or dataclasses for data objects — no bare dicts crossing boundaries.

## Comments
- Comments explain *why*, not *what*. Code explains what.
- If you're commenting what a block does, extract it into a named function instead.
- TODOs: `# TODO(shri): <what> — <why not done now>`

## What not to do
- No magic numbers or hardcoded strings.
- No dead code — delete it, git has history.
- No functions over ~40 lines without a good reason.
- No suppressed errors.
- No unused imports.