---
name: git-allrounder
description: >
  Full Git lifecycle manager. Use this skill whenever a project is being created (triggers git init),
  whenever Claude is about to implement a feature, fix a bug, or make any non-trivial code change
  (triggers branch creation for sandboxed work), and whenever changes are ready to commit (triggers
  Conventional Commits formatting). Also triggers for merges, PR summaries, and branch cleanup.
  Activate on phrases like "start a project", "new project", "implement feature", "fix bug",
  "add X", "create X", "refactor", "write tests", "commit", "merge", "push", or any task that
  involves writing code. Never skip this skill when code changes are involved.
---

# Git All-Rounder Skill

End-to-end Git workflow covering project init, feature branching, commit formatting, human-verified merges, and cleanup.

---

## Phase 1 — Project Initialization

**Trigger:** User starts a new project or asks Claude to scaffold one.

```bash
git init
git add .
git commit -m "chore: initial project scaffold"
```

Steps:
1. Run `git init` in the project root.
2. Create a `.gitignore` appropriate to the tech stack (Node, Python, etc.) if one doesn't exist.
3. Stage all initial files and make the first commit using the `chore:` type (see Commit Standards below).
4. Announce: "Git repo initialized. Branch: `main`. Ready to work."

---

## Phase 2 — Feature / Fix Branches

**Trigger:** Any new feature, bug fix, refactor, or isolated chunk of work.

### Branch Naming Convention

| Work type   | Branch prefix       | Example                        |
|-------------|---------------------|--------------------------------|
| Feature     | `feat/`             | `feat/user-auth`               |
| Bug fix     | `fix/`              | `fix/null-pointer-login`       |
| Refactor    | `refactor/`         | `refactor/db-connection-pool`  |
| Docs        | `docs/`             | `docs/api-reference`           |
| Tests       | `test/`             | `test/checkout-flow`           |
| Chore/infra | `chore/`            | `chore/update-dependencies`    |

### Workflow

```bash
# 1. Always branch from main (or the agreed base branch)
git checkout main
git pull origin main          # if remote exists

# 2. Create and switch to the new branch
git checkout -b <prefix/short-description>

# 3. Work, stage, and commit incrementally (see Commit Standards)
git add <files>
git commit -m "<type>[scope]: <description>"
```

Announce the branch name to the user: `"Working on branch: feat/user-auth"`

---

## Phase 3 — Commit Standards (Conventional Commits)

Read `references/commit-standards.md` for full spec. Summary:

### Format
```
<type>[optional scope]: <description>

[optional body]

[optional footer — BREAKING CHANGE: ...]
```

### Allowed Types
- `feat` — new feature
- `fix` — bug fix
- `docs` — documentation only
- `style` — formatting, whitespace (no logic change)
- `refactor` — code restructure (not a fix, not a feature)
- `perf` — performance improvement
- `test` — adding or correcting tests
- `chore` — build process, tooling, dependencies

### Rules
1. Description in **imperative mood**: "add login" not "added login".
2. No period at the end of the description line.
3. Keep description under 72 characters.
4. For breaking changes add footer: `BREAKING CHANGE: <explanation>`.

### Examples
```
feat(auth): add JWT refresh token support
fix(cart): prevent duplicate item addition on rapid click
docs(readme): update installation steps for Windows
chore: upgrade eslint to v9
```

---

## Phase 4 — Human Verification & Merge

**Never merge autonomously.** Always pause and ask for explicit approval.

### Pre-merge checklist (run and show output to user)
```bash
git diff main...<current-branch> --stat        # what changed
git log main..<current-branch> --oneline       # commits on this branch
```

Present a summary:
```
Branch:   feat/user-auth  →  main
Commits:  3
Files:    src/auth.js, tests/auth.test.js, docs/auth.md
──────────────────────────────────────────────────────
Ready to merge. Please review the diff above.
Type "merge" to proceed, or give feedback to revise.
```

Wait for the user to say **"merge"** (or equivalent approval) before proceeding.

### Merge (after approval)
```bash
git checkout main
git merge --no-ff <branch-name> -m "feat(auth): merge user auth feature"
```

Use `--no-ff` to preserve branch history.

### Post-merge cleanup
```bash
git branch -d <branch-name>           # delete local branch
# git push origin --delete <branch>  # uncomment if remote exists
```

Announce: "Merged and branch deleted. Back on `main`."

---

## Phase 5 — Status & Hygiene

Run these proactively to keep the user informed:

```bash
git status                  # before starting work
git log --oneline -10       # after merging, to show recent history
git branch                  # to confirm current branch
```

---

## Edge Cases

- **Uncommitted changes when switching branches:** stash them first.
  ```bash
  git stash push -m "wip: <description>"
  git checkout <target-branch>
  # ... do work ...
  git stash pop
  ```
- **Merge conflicts:** surface the conflict to the user, do not auto-resolve. Show `git diff` and ask which version to keep.
- **Remote not configured:** note it but don't block local workflow. Remind user to add remote when ready: `git remote add origin <url>`.
- **Monorepo / nested projects:** init git at the repo root only. Use scopes in commits to indicate which package/service changed.

---

## Quick Reference

| Situation                     | Command / Action                              |
|-------------------------------|-----------------------------------------------|
| New project                   | `git init` → initial commit                   |
| Starting a feature            | `git checkout -b feat/<name>`                 |
| Committing work               | Conventional Commits format (Phase 3)         |
| Ready to merge                | Show diff → wait for "merge" → `--no-ff` merge |
| After merge                   | Delete branch, stay on `main`                 |
| Unsaved work, need to switch  | `git stash push` → switch → `git stash pop`   |

For full Conventional Commits spec → `references/commit-standards.md`
