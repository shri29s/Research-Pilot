# Conventional Commits — Full Reference

Source: Conventional Commits specification (https://www.conventionalcommits.org)

---

## Full Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

---

## Types

| Type       | When to use                                                                 |
|------------|-----------------------------------------------------------------------------|
| `feat`     | A new feature visible to users or consumers of the API                      |
| `fix`      | A bug fix                                                                   |
| `docs`     | Documentation changes only (README, JSDoc, OpenAPI spec, etc.)              |
| `style`    | Whitespace, formatting, missing semicolons — no logic change                |
| `refactor` | Code restructuring that is neither a fix nor a feature                      |
| `perf`     | Performance improvement (faster query, reduced memory, etc.)                |
| `test`     | Adding missing tests or correcting existing ones                            |
| `chore`    | Build system, tooling, dependency bumps, CI config, non-src housekeeping    |

---

## Scope

Optional. Identifies the module, component, or layer affected.

- Write in lowercase, no spaces: `auth`, `cart`, `db`, `api`, `ui`
- Keep it short and consistent across the codebase

```
feat(auth): add OAuth2 provider support
fix(cart): handle empty cart state on checkout
```

---

## Description Rules

1. Imperative mood: `add`, `fix`, `remove` — not `added`, `fixes`, `removed`
2. Lowercase first letter
3. No period at end
4. ≤ 72 characters
5. Complete the sentence: *"If applied, this commit will…"*

---

## Body (optional)

- Separated from description by a blank line
- Explain **what** and **why**, not **how**
- Wrap at 72 characters per line

```
feat(payments): add retry logic for failed transactions

Payment processor occasionally returns transient 503 errors.
Added exponential backoff with 3 retries before surfacing
the error to the user.
```

---

## Footers (optional)

- Separated from body by a blank line
- Format: `Token: value` or `Token #value`

### Breaking Changes

```
feat(api)!: change authentication endpoint path

BREAKING CHANGE: /auth/login is now /v2/auth/login.
All clients must update their base URL.
```

The `!` after the type is optional but recommended for visibility.

### Issue References

```
fix(login): prevent session fixation on re-auth

Closes #142
```

---

## Common Mistakes to Avoid

| Wrong                              | Right                              |
|------------------------------------|------------------------------------|
| `Added user login feature`         | `feat(auth): add user login`       |
| `fixes bug`                        | `fix(api): handle null response`   |
| `update stuff`                     | `chore: update eslint config`      |
| `feat: Add Login.`                 | `feat: add login` (no capital, no period) |
| Committing everything in one shot  | Small, atomic commits per concern  |

---

## Atomicity Principle

Each commit should represent **one logical change**. If you find yourself writing "and" in a commit message, split it into two commits.

```
# Too broad
feat(checkout): add cart summary, fix tax calculation, update styles

# Better
feat(checkout): add cart item summary panel
fix(checkout): correct tax rounding for fractional amounts
style(checkout): align summary total to right edge
```
