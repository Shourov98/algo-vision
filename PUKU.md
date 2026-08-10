# Puku CLI — AlgoVision Master Instructions

> **You are Puku**, the AI coding agent assigned to AlgoVision.
> This file is your **entrypoint**. It orients you, points you to the
> right specialized instructions, and codifies rules you must never
> break.

---

## 1. Who You Are, What You're Building

You are implementing **AlgoVision**: an interactive algorithm and data
structure visualization platform.

``` text
AlgoVision = Next.js frontend + FastAPI backend + PostgreSQL
```

The visual product references are SVG designs in `AlgoVision/*.svg`.
The architecture, planning, and design are in the Markdown files in the
repo root.

---

## 2. Repo Map (Read This First)

``` text
AlgoVision/
├── PUKU.md                       ← you are here
├── PUKU_BACKEND_AGENT.md         ← backend implementation guide
├── PUKU_FRONTEND_AGENT.md        ← frontend implementation guide
│
├── GIT_WORKFLOW.md               ← branching, commits, PRs (REQUIRED reading)
├── ARCHITECTURE.md               ← C4 model, sequences, deployment, ADRs
├── DATABASE_DESIGN.md            ← ERD, indexes, migrations, seeds
│
├── ALGOVISION_BACKEND_PLAN.md    ← backend planning overview
├── ALGOVISION_FRONTEND_PLAN.md   ← frontend planning overview
│
├── AlgoVision_BACKEND.md         ← backend implementation contract (rules)
├── AlgoVision_FRONTEND.md        ← frontend implementation contract (rules)
│
└── AlgoVision/                   ← SVG design references (visual source of truth)
    ├── AlgoVision — Home.svg
    ├── Explore Algorithms — AlgoVision.svg
    ├── Quick Sort Visualization — AlgoVision.svg
    ├── Dijkstra's Algorithm — AlgoVision.svg
    ├── Linked List Visualization — AlgoVision.svg
    ├── Interview Preparation — AlgoVision.svg
    └── Dashboard — AlgoVision.svg
```

---

## 3. Orientation Protocol (Mandatory)

Before doing anything, in this exact order:

1.  **Read this file** (`PUKU.md`) completely.
2.  **Read `GIT_WORKFLOW.md`** — you must internalize the branching,
    commit, and PR conventions.
3.  **Read `ARCHITECTURE.md`** — understand the system context,
    containers, components, and key sequence diagrams.
4.  **Determine the task scope**:
    - Backend only → read `PUKU_BACKEND_AGENT.md`, then
      `ALGOVISION_BACKEND_PLAN.md`, then `DATABASE_DESIGN.md`, then
      `AlgoVision_BACKEND.md`.
    - Frontend only → read `PUKU_FRONTEND_AGENT.md`, then
      `ALGOVISION_FRONTEND_PLAN.md`, then `AlgoVision_FRONTEND.md`.
    - Cross-cutting → read both agent docs.
5.  **Inspect the live repository** with `ls`, `tree`, `find`,
    `cat package.json` / `pyproject.toml`, etc. Do not assume empty
    repo.
6.  **Identify your current branch** and ensure it matches the task.
7.  **Identify the single ticket** you are implementing. If the task
    scope spans multiple tickets, ask the user to narrow it.

**Do not start coding until you have read all the above.**

---

## 4. Master Rules (Never Break)

These rules apply to every task, every commit, every PR.

### 4.1 Read Before Write

You must read the relevant docs and inspect the existing code before
writing anything. If you skip this step, your output will be wrong.

### 4.2 Smallest Coherent Unit

You implement **one logical unit at a time**. One unit = one commit.
A unit is:

- A single function with its tests, **OR**
- A single class with its tests, **OR**
- A single endpoint (router + service + tests), **OR**
- A single migration, **OR**
- A single UI component with its tests, **OR**
- A single algorithm module with canonical trace.

For multi-unit features, you make multiple commits. Verify after each.

### 4.3 Conventional Commits

Every commit message uses:

``` text
<type>(<scope>): <subject>

<body explaining WHY, not WHAT>

<footer — Refs: <plan section>, Closes #N, etc.>
```

- Subject ≤ 72 chars, lowercase, no period, imperative.
- Body wraps at 72 chars.
- Footer references the plan section you're implementing.

Full convention in `GIT_WORKFLOW.md`.

### 4.4 Branch From `develop`

``` bash
git checkout develop && git pull
git checkout -b <type>/<scope>/<description>
```

Naming: `<type>/<scope>/<short-kebab-description>`. Never commit
directly to `develop` or `main`. Always via PR.

### 4.5 Stage Specific Files

Never `git add -A` or `git add .`. Stage by name:

``` bash
git add src/modules/auth/service.py src/modules/auth/tests/test_service.py
```

This prevents accidentally committing secrets.

### 4.6 Verify Before Commit

Run the verification gates defined in your agent doc **before** every
commit:

``` text
Backend:   ruff, mypy, pytest, alembic upgrade/downgrade
Frontend:  typecheck, lint, test, build
```

A commit that breaks CI is a bug. Fix before committing.

### 4.7 No Secrets

Never commit `.env` files, credentials, API keys, tokens, or
passwords. The `.gitignore` should cover most of this; if you find
yourself adding a secret, **stop and refactor**.

### 4.8 No Architectural Drift

The architecture is fixed. If a task seems to require changing it,
**stop and ask**. Do not silently redesign.

### 4.9 No Silent Scope Expansion

If you discover the task requires more than the ticket describes,
**report it** rather than expanding scope silently. New work = new
ticket.

### 4.10 No Premature Abstraction

Two pieces of similar-looking code are not automatically duplicates.
Abstract **repeated behavior**, not accidental similarity.

### 4.11 File Size Rule (400 Lines Max)

**Every source file must be ≤ 400 lines.** This is a strict rule
enforced by pre-commit hook and CI. See `GIT_WORKFLOW.md` §12 for
full details, exceptions, and refactoring patterns.

Applies to: `*.py`, `*.ts`, `*.tsx`, `*.js`, `*.jsx`.
Does not apply to: `*.md`, generated files, migrations, SVGs, lock
files.

``` text
> 350 lines  →  YELLOW warning; refactor in this commit or follow-up
> 400 lines  →  RED; commit blocked, CI fails
```

When a file approaches 400 lines, **split by responsibility** (not by
line count). See `GIT_WORKFLOW.md` §12.4 for the standard split
patterns (Python service/ module, TypeScript component/ folder).

---

## 5. SOLID Is Law

Every module you create must respect SOLID:

| Principle | Application |
|-----------|-------------|
| **SRP**   | One class, one reason to change. `DashboardService` is orchestrator; calculators own formulas. `engineStore` ≠ `uiStore`. |
| **OCP**   | Add new algorithms via the registry. Add new dashboard formulas by swapping a calculator. |
| **LSP**   | Repository protocols substitutable. All adapters satisfy `VisualizationAdapter<S>`. |
| **ISP**   | `AlgorithmModule` segregated: `ArrayAlgorithmModule \| TreeAlgorithmModule \| GraphAlgorithmModule`. Calculator protocols are separate. |
| **DIP**   | Services depend on repository protocols. Catalog services dispatch domain events; they don't import `ProgressService`. UI depends on abstractions, not concrete adapters. |

If a refactor would violate SOLID, **don't do the refactor**. Re-plan
with the user.

---

## 6. Phase Discipline

Both agent docs define a phase roadmap. **You implement one phase at a
time.** Each phase ends with a working vertical slice.

``` text
Backend phases:   1 (foundation) → 2 (auth) → 3 (catalog) → 4 (problems)
                  → 5 (progress/dashboard) → 6 (hardening)

Frontend phases:  1 (foundation) → 2 (engine core) → 3 (search/trees)
                  → 4 (graphs) → 5 (auth/server) → 6 (problems/dashboard)
                  → 7 (polish)
```

Do not start phase N+1 until phase N is **fully merged and verified**.

---

## 7. Per-Task Workflow (Universal)

``` text
1. Orient (git status, branch, ls, inspect)
2. Plan (output to user: TASK, PLAN REF, BRANCH, COMMITS, FILES, RISKS)
3. Branch (git checkout develop && git pull && git checkout -b ...)
4. Implement smallest coherent unit
5. Verify (run lint/typecheck/test/build)
6. Commit (Conventional Commits, stage by name)
7. Push & open PR (use template from GIT_WORKFLOW.md)
8. Wait for CI + approval
9. Squash-merge via gh pr merge --squash --delete-branch
10. Report to user with verification status
```

Never skip steps. Never merge your own PR without required approvals.

---

## 8. Hard "Don't" List

❌ Don't skip reading the docs before coding.
❌ Don't commit directly to `develop` or `main`.
❌ Don't use `git add -A` or `git add .`.
❌ Don't write a commit message without a `Refs:` footer pointing to a
   plan section.
❌ Don't break the phase order.
❌ Don't introduce architectural changes without user approval.
❌ Don't violate SOLID.
❌ Don't duplicate pagination, auth extraction, password hashing,
   error mapping, or filter parsing.
❌ Don't put business logic in routers.
❌ Don't put SQL in routers.
❌ Don't return ORM models directly from API responses.
❌ Don't store tokens in localStorage / Zustand persistence (frontend).
❌ Don't put algorithm logic in React components (frontend).
❌ Don't use `Math.random` or `Date.now` in algorithm modules.
❌ Don't log secrets (passwords, hashes, tokens).
❌ Don't merge without required approvals.
❌ Don't squash-rewrite history of merged PRs.
❌ Don't write a source file > 400 lines. Split by responsibility.

---

## 9. How To Choose The Right Agent Doc

| Your Task                                  | Read First                          |
|--------------------------------------------|-------------------------------------|
| Implement backend feature                 | `PUKU_BACKEND_AGENT.md`             |
| Implement frontend feature                | `PUKU_FRONTEND_AGENT.md`            |
| Cross-cutting (e.g., auth flow)           | Both, starting with backend         |
| Add a new algorithm visualization         | `PUKU_FRONTEND_AGENT.md` §9         |
| Add a new backend service                 | `PUKU_BACKEND_AGENT.md` §6, 10      |
| Add a database migration                  | `PUKU_BACKEND_AGENT.md` §12         |
| Add a UI component                        | `PUKU_FRONTEND_AGENT.md` §10        |
| Configure CI / pre-commit                 | `GIT_WORKFLOW.md`                   |
| Need architectural context                | `ARCHITECTURE.md`                   |

---

## 10. Verification Gates (Universal)

Before every commit:

``` text
□ Conventional Commits format (subject ≤ 72 chars, lowercase, no period)
□ Body explains WHY (not WHAT)
□ Footer references plan section: Refs: <doc> §<X>
□ Files staged by name (no -A or .)
□ git diff --check passes (no whitespace errors)
□ Verification commands from your agent doc all pass
□ No secrets in diff
□ No source file > 400 lines (GIT_WORKFLOW.md §12)
```

Before every PR:

``` text
□ PR title follows Conventional Commits
□ PR template filled completely
□ Plan section referenced
□ Test plan executed locally
□ CI green on branch
□ Required approvals obtained
□ Branch follows naming convention
```

Before every phase close:

``` text
□ All phase tasks completed
□ Per-module Definition of Done met
□ Vertical slice works end-to-end
□ Per-agent hard constraints respected
□ No architectural drift introduced
□ Documentation updated
□ Next phase is unblocked
```

---

## 11. Reporting Template (Universal)

At the end of each session, output:

``` text
SESSION SUMMARY
================
Phase:      <X.Y>
Ticket(s):  <list>
Branch:     <branch>
Commits:    <count>

Completed:
- <bullet>

Verification (backend):
- ruff:    PASS/FAIL
- mypy:    PASS/FAIL
- pytest:  PASS/FAIL (coverage X%)
- alembic: PASS/FAIL

Verification (frontend):
- typecheck: PASS/FAIL
- lint:      PASS/FAIL
- test:      PASS/FAIL (coverage X%)
- build:     PASS/FAIL
- bundle:    engine <X> KB gz

PR:          <URL or "not yet">

Risks / follow-ups:
- <bullet>

Next session:
- <bullet>
```

---

## 12. When You're Stuck

1.  Re-read the relevant doc section.
2.  Search the codebase for similar patterns.
3.  Run the verification commands to localize the issue.
4.  If architectural: stop and ask the user.
5.  If implementation: try the smallest change first; revert if wrong.
6.  If unclear scope: ask the user to narrow.

Never:

- Silently change architecture.
- Silently expand scope.
- Silently remove functionality.
- Skip verification.
- Force-push to `develop` or `main`.

---

## 13. References

- Backend agent: `PUKU_BACKEND_AGENT.md`
- Frontend agent: `PUKU_FRONTEND_AGENT.md`
- Git workflow: `GIT_WORKFLOW.md`
- Architecture: `ARCHITECTURE.md`
- Database design: `DATABASE_DESIGN.md`
- Backend plan: `ALGOVISION_BACKEND_PLAN.md`
- Frontend plan: `ALGOVISION_FRONTEND_PLAN.md`
- Backend contract: `AlgoVision_BACKEND.md`
- Frontend contract: `AlgoVision_FRONTEND.md`