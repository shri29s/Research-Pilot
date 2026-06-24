# WORKFLOW.md
> Read this when committing, branching, or pushing. Also read before documenting a decision.

---

## Commit flow (every unit of work)

After human approval, invoke the `git-allrounder` skill:
- Stage changed files
- Generate a conventional commit message
- Commit and push to the current branch

### Commit message format
```
type(scope): short imperative description

- what changed
- why, if non-obvious
```

**Types:** `feat` `fix` `refactor` `docs` `test` `chore` `style`
**Examples:**
- `feat(auth): add JWT refresh token rotation`
- `fix(db): handle null user on login`
- `docs(decisions): add ADR for async task queue choice`

---

## Branch rules
- `main` is always runnable. Never push broken code.
- Branch naming: `feat/short-name`, `fix/short-name`, `chore/short-name`
- One logical change per branch where possible.

## Before every push
- [ ] Linter passes
- [ ] Tests pass in a clean environment
- [ ] No `.env`, `__pycache__`, or build artifacts staged

---

## Decision documentation

Append to `docs/DECISIONS.md` **in the same commit** as the code it governs, when:
- A library or framework was chosen over alternatives
- An architecture pattern was picked
- A data model was designed with tradeoffs
- A performance or security tradeoff was made
- An alternative was explicitly rejected

### ADR format
```markdown
## [Short title]

**Date:** YYYY-MM-DD
**Status:** decided | revisit | superseded by [title]

**Context:**
What forced this decision?

**Options considered:**
- Option A — tradeoff
- Option B — tradeoff

**Decision:**
What was chosen and why.

**Consequences:**
What this enables. What it constrains.
```

---

## Session start
Read `docs/CONTEXT.md` to orient before doing anything.

## Session end
Update `docs/CONTEXT.md` with: what was built, what's next, any open questions.