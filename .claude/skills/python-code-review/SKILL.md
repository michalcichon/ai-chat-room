---
name: python-code-review
description: Review a Python diff, branch, PR or path for good practices and architecture violations (layering, dependency direction, ports & adapters, etc.). Use when the user asks for a code review, "review my changes", "check architecture", or before merging. Works in any Python repo; it discovers the repo's own architecture rules instead of assuming them.
---

# Python code review

Report only. Do not edit code unless the user asks.

## 1. Scope

- Target = what the user named (PR number, branch, path). Otherwise the working diff: `git diff HEAD` plus untracked files (`git status --short`).
- No changes found → say so and stop.
- Read each changed file fully, not just hunks. Grep callers of any changed public function/class.

## 2. Discover the architecture (never assume)

Look, in order, for the rules this repo declares:
1. `CLAUDE.md`, `AGENTS.md`, `README*`, `docs/`, ADRs (`docs/adr`, `adr/`) — sections named architecture/layers/structure.
2. Enforced config: `importlinter`/`.importlinter`, `[tool.importlinter]`, `tach.toml`, `pyproject.toml` (ruff `flake8-tidy-imports`, `banned-api`), `tox`/`Makefile` lint targets.
3. Directory layout (`domain/`, `ports/`, `adapters/`, `services/`, `api/`, `infra/`, …) and the existing import graph.

Write down for yourself a short rule list: layers, allowed dependency directions, where I/O lives, where wiring/composition lives. If rules are only implied by layout, state your inference at the top of the review and mark related findings "inferred rule".
If nothing can be inferred, skip section 3 and say so.

Check the import graph of changed files:
`grep -nE '^(from|import) ' <file>` and compare against the rules.

## 3. Architecture checks

- **Dependency direction**: inner layers (domain/core) must not import outer ones (adapters, frameworks, DB/HTTP/SDK clients, CLI/UI libs, env/config).
- **Ports/interfaces**: core talks to the outside only via abstractions it owns (Protocol/ABC); adapters implement them. Flag adapters importing other adapters.
- **Leaking details**: framework/ORM/transport types or exceptions crossing a boundary; domain objects serialized ad hoc in adapters; business rules living in adapters/handlers.
- **Wiring**: concrete classes constructed only at the composition root / entry points, not deep inside core logic.
- **New code placement**: does the new module sit in the layer matching its responsibility?
- **Docs drift**: structure changed but README/architecture docs/diagrams not updated.

## 4. Good-practice checks

Correctness & robustness
- Mutable default args, late-binding closures, bare/over-broad `except`, swallowed errors, `assert` for runtime validation.
- Missing validation at trust boundaries (network, CLI, env, files); secrets in code/logs.
- Async: blocking calls in `async def`, un-awaited coroutines, orphaned tasks (`create_task` without reference/handling), missing cancellation/cleanup, shared state without care.
- Resource handling: files/sockets/clients without context managers or close.

Design & style
- Type hints on public APIs; `Protocol`/`dataclass`/`Enum` over loose dicts/strings for domain concepts.
- Small single-purpose functions; no god classes; no duplicated logic that already exists elsewhere in the repo (grep before claiming).
- Naming, dead code, commented-out code, unused imports, speculative abstractions.
- `logging` over `print` in non-CLI code; no global mutable state; config via injection, not scattered `os.environ`.
- Prefer stdlib/existing deps over new ones; check new dependencies are declared (`pyproject.toml`/lock).

Tests
- New behavior has tests at the right level (domain logic unit-tested without adapters/mocks of internals; adapters tested at their boundary).
- Tests are deterministic (no real network/time/sleep), assert behavior not implementation.
- If feasible run the repo's own checks (`pytest`, `ruff`, `mypy`/`pyright`, `lint-imports`) — detect from pyproject/Makefile; report failures verbatim. Skip silently-unavailable tools, but say they were skipped.

## 5. Output

Be concise; only real issues, no praise padding, no style nitpicks a formatter would fix.

```
## Architecture rules used
<2-5 lines: rules found + source, or "inferred from layout">

## Findings
### Must fix        (violations of architecture, bugs, security)
- `path:line` — problem. Why it matters. Suggested fix (one line).
### Should fix      (good-practice issues, missing tests)
- ...
### Nits            (optional, max 3)
- ...

## Verdict
Approve / Approve with changes / Request changes — one sentence.
```

Rules: every finding cites `path:line`; verify by reading code before reporting; if unsure, label "possible" and say what would confirm it; if a section is empty write "none".

## 6. Apply mode (only when asked: "apply", "fix", or run from CI)

Default is report-only. In apply mode, after the review:
- Fix only Must fix / Should fix findings that are unambiguous and local. Leave design-level or uncertain ones as comments.
- Re-run the repo's tests/linters; if they fail because of your change, revert that fix.
- One commit per logical fix (never `--amend`, never force-push, never touch the default branch; commit on the current PR/feature branch). Message format:

```
<short summary line>

What: <what was changed, concretely: files/behavior>

Why: <why it was changed: the rule, bug or risk it addresses>
```

- Push to the current branch, then post the verdict and any unfixed findings as a PR comment (`gh pr comment`) when `gh` is available.
