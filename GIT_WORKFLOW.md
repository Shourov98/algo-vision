# AlgoVision Git Workflow

> How we branch, commit, review, and merge. Designed for:
> - **Function-completion commits** — every meaningful unit of work is
>   its own commit.
> - **Easy code review** — small, focused, self-contained PRs.
> - **Traceability** — every commit references a plan section.

---

## 1. Branch Strategy — Lightweight Git Flow + Frontend/Backend Split

AlgoVision uses **one integration branch per domain** to keep
frontend and backend work isolated while they evolve in parallel.

``` text
main                          Production-ready. Protected. Tagged per release.
└── develop                   Cross-cutting integration (default for general PRs)
    ├── dev-frontend          Frontend integration (features F1.*–F7.*)
    │     └── feat/<scope>/<ticket>    Frontend feature work
    ├── dev-backend           Backend integration (features B1.*–B6.*)
    │     └── feat/<scope>/<ticket>    Backend feature work
    └── (cross-cutting X.* features branch from develop directly)
```

### 1.1 Branch Topology

``` text
main                                (canonical docs only; protected)
 │
 └── develop                        (cross-cutting integration)
      │
      ├── dev-frontend              (frontend integration)
      │     │
      │     ├── feat/algorithms/quick-sort-module        → PR → dev-frontend
      │     ├── feat/auth/login-page                     → PR → dev-frontend
      │     └── feat/visualization/array-adapter         → PR → dev-frontend
      │
      ├── dev-backend               (backend integration)
      │     │
      │     ├── feat/auth/login-endpoint                → PR → dev-backend
      │     ├── feat/algorithms/list-endpoint           → PR → dev-backend
      │     └── feat/dashboard/streak-calculator         → PR → dev-backend
      │
      └── (cross-cutting X.* work)
            │
            ├── feat/ci/add-ci-pipeline                 → PR → develop
            └── chore/deps/bump-fastapi                  → PR → develop
```

### 1.2 Branch Routing Rule (STRICT)

When implementing a feature, the **base branch and target branch** are
determined by the feature ID prefix in `FEATURE_LIST.md`:

| Feature ID prefix       | Base branch    | Target branch | Read these docs                  |
|-------------------------|----------------|---------------|----------------------------------|
| `B1.*`, `B2.*`, ..., `B6.*` | `dev-backend`  | `dev-backend` | `PUKU_BACKEND_AGENT.md`, `ALGOVISION_BACKEND_PLAN.md`, `DATABASE_DESIGN.md`, `AlgoVision_BACKEND.md` |
| `F1.*`, `F2.*`, ..., `F7.*` | `dev-frontend` | `dev-frontend`| `PUKU_FRONTEND_AGENT.md`, `ALGOVISION_FRONTEND_PLAN.md`, `AlgoVision_FRONTEND.md` |
| `X.*`                  | `develop`      | `develop`     | Both agent docs                  |

**Violations:**

- ❌ A backend feature (B-prefix) PR'd to `dev-frontend` or `develop`
  → blocked.
- ❌ A frontend feature (F-prefix) PR'd to `dev-backend` or `develop`
  → blocked.
- ❌ A cross-cutting feature (X-prefix) PR'd to `dev-frontend` or
  `dev-backend` → blocked (unless it touches only one side; in which
  case re-classify as F or B and follow the appropriate routing).

**How Puku decides at runtime:**

``` bash
# Pseudo-code for branch selection
case $FEATURE_ID in
  B*)  BASE=dev-backend; TARGET=dev-backend ;;
  F*)  BASE=dev-frontend; TARGET=dev-frontend ;;
  X*)  BASE=develop; TARGET=develop ;;
  *)   echo "Unknown feature ID; ask user."; exit 1 ;;
esac
```

### 1.3 Promote-to-Develop Flow

`dev-frontend` and `dev-backend` are kept aligned with `develop`
through **periodic fast-forwards**. The cadence:

``` text
When a phase is complete and verified on its dev branch:
  dev-frontend ──ff──▶ develop         (or merge --no-ff if histories diverged)
  dev-backend  ──ff──▶ develop         (same)

When both dev branches are green on develop and have completed their
phase, cut release:
  develop ──cut release/v0.X.Y──▶ release/v0.X.Y ──merge──▶ main + tag
```

The cadence is **not** "every commit". It's **per verified phase**
(see `FEATURE_LIST.md` §6 for what "complete" means for each phase).

### 1.4 Why Two Dev Branches?

1. **Isolation**: frontend and backend can iterate without stepping on
   each other's CI.
2. **Clean diffs**: a frontend PR is reviewable without backend noise;
   vice versa.
3. **Parallelism**: two agents (or two developers) can work
   simultaneously without forced merges.
4. **Cleaner history**: each integration branch has only commits
   relevant to its domain.

**Tradeoff acknowledged:** sync merges between `dev-frontend` and
`dev-backend` are required at phase boundaries. This is acceptable
because each phase has a clear Definition of Done.

**Release flow:**

``` text
develop ──cut release/v0.1.0──▶ release/v0.1.0
                                       │
                            hotfix only allowed here
                                       │
                                       ▼
                              merge → main + tag
                                       │
                                       ▼
                              merge back into develop
```

For most work, the lifecycle is simple:

``` text
develop ──branch──▶ feat/... ──commit...commit──PR──▶ develop
```

---

## 2. Branch Naming Convention

``` text
<type>/<scope>/<short-kebab-description>
```

**Type** (matches Conventional Commits):

``` text
feat      New user-facing functionality
fix       Bug fix
refactor  Internal change with no behavior change
perf      Performance improvement
test      Adding or fixing tests
docs      Documentation only
chore     Tooling, deps, config
ci        CI/CD pipeline changes
```

**Scope** (one of):

``` text
auth            users           algorithms
data-structures problems        progress
dashboard       roadmap         visualization
engine          adapters        player
shell           api             db
seed            migration       infra
```

**Examples:**

``` text
feat/auth/register-endpoint
feat/auth/login-endpoint
feat/auth/refresh-token-rotation
feat/algorithms/list-endpoint
feat/algorithms/quick-sort-module
feat/visualization/array-adapter
feat/visualization/player-state-machine
fix/dashboard/streak-calculation
fix/auth/refresh-token-expiry-edge-case
refactor/backend/split-dashboard-service
refactor/visualization/split-engine-and-ui-stores
perf/dashboard/index-user-progress-tables
test/algorithms/bubble-sort-canonical-trace
docs/backend/api-contract
docs/frontend/visualization-engine
chore/deps/bump-fastapi-0.115
ci/backend/add-migration-verify-job
```

---

## 3. Commit Convention — Conventional Commits

### 3.1 Format

``` text
<type>(<scope>): <short summary>

<body — explain WHY, not WHAT>

<footer — refs, breaking changes, co-authors>
```

- **Subject** is imperative, lowercase, no period, ≤72 chars.
- **Body** explains motivation, trade-offs, design choices. Wrap at
  ~72 chars. Reference plan sections where relevant.
- **Footer** for `Refs:`, `Closes #N`, `BREAKING CHANGE:`,
  `Co-authored-by:`.

### 3.2 One Function = One Commit (Guideline)

A commit should be the smallest **logical unit** that:

- Compiles / lints clean
- Has tests if it has logic
- Could be reverted without breaking unrelated work
- Maps to one or more plan sections

For multi-function features, split into multiple commits:

``` text
# Example: implementing login
1. feat(auth): add Argon2id password hashing utility
2. feat(auth): implement login service method
3. feat(auth): add /auth/login router endpoint
4. feat(auth): add login integration tests
5. docs(auth): document login API contract
```

Each commit is reviewable in < 400 lines and has a single purpose.

### 3.3 Examples

**Adding an algorithm module:**

``` text
feat(visualization): add bubble sort event generator

Implements the pure AlgorithmEvent[] generator for bubble sort.
Uses stable element IDs derived from the input array index + run
seed. Emits compare, swap, mark, and complete events.

Refs: ALGOVISION_FRONTEND_PLAN.md §6.5, §6.6
Refs: ALGOVISION_FRONTEND_PLAN.md §8 (state ownership)
```

**Adding a service method:**

``` text
feat(algorithms): add get_by_slug service method

Returns AlgorithmDetail with category, topics, current code version
per language, and (if authenticated) user_progress. Cached at HTTP
layer via ETag on algorithms.updated_at.

Refs: ALGOVISION_BACKEND_PLAN.md §6 (AlgorithmService)
Refs: ALGOVISION_BACKEND_PLAN.md §7 (API design)
Refs: DATABASE_DESIGN.md §5 (indexes)
```

**Fix:**

``` text
fix(dashboard): correct streak calculation across midnight UTC

Streak previously counted calendar days in user's local timezone,
producing off-by-one errors near midnight. Now uses date_trunc('day',
completed_at AT TIME ZONE 'UTC') consistently.

Refs: ALGOVISION_BACKEND_PLAN.md §6 (DashboardService)
```

**Refactor (SOLID fix):**

``` text
refactor(backend): split DashboardService into focused calculators

Replaces single DashboardService with 5 components:
- DashboardAggregator (orchestrator)
- ReadinessCalculator
- SkillMapper
- FocusAreaSelector
- StreakCalculator

Each calculator has one reason to change. DashboardAggregator now
depends on calculator protocols (Dependency Inversion), enabling
stub implementations in tests.

Refs: ALGOVISION_BACKEND_PLAN.md §6 (SOLID map)
Refs: ARCHITECTURE.md §7 (ADR-002)
```

**Test only:**

``` text
test(visualization): add canonical trace test for bubble sort

Locks the event count and order for input [5,2,8,1,4]. CI fails if
future refactors change the trace. This is the contract the
visualization engine depends on.

Refs: ALGOVISION_FRONTEND_PLAN.md §6.10 (invariants)
Refs: ALGOVISION_FRONTEND_PLAN.md §19 (testing strategy)
```

### 3.4 Allowed Types

``` text
feat, fix, refactor, perf, test, docs, chore, ci, build, style, revert
```

`style` is reserved for formatting-only changes (whitespace, imports).

---

## 4. Pull Request Workflow

### 4.1 PR Title

Same format as commit subject:

``` text
feat(auth): implement login endpoint with Argon2id
```

### 4.2 PR Template

Place at `.github/pull_request_template.md`:

``` markdown
## Summary

<!-- 2-4 bullets describing what this PR does and why -->

-

## Plan Reference

<!-- Reference the relevant plan section -->

- Section:
- ADR (if applicable):

## Test Plan

<!-- Checklist of what was tested -->

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated (if applicable)
- [ ] Manual testing performed (describe)
- [ ] E2E tests added/updated (if applicable)

## Checklist

- [ ] Branch follows naming convention (`<type>/<scope>/<description>`)
- [ ] Commits follow Conventional Commits format
- [ ] No unrelated changes included
- [ ] Lint passes (`ruff check`, `eslint`)
- [ ] Typecheck passes (`mypy src/`, `tsc --noEmit`)
- [ ] Tests pass and coverage maintained
- [ ] Migrations reviewed (if schema changed)
- [ ] No secrets committed
- [ ] Self-reviewed

## Screenshots / Recordings

<!-- For UI changes only -->

## Risks

<!-- Known risks, edge cases, follow-ups -->

## Follow-ups

<!-- TODOs intentionally deferred to separate PRs -->
```

### 4.3 Review Process

- **One approval** required for `feat/*`, `fix/*`, `refactor/*`.
- **Two approvals** for changes touching `core/`, `auth/`,
  `migrations/`, or CI config.
- **Author** must self-review before requesting review.
- **Reviewer** focuses on:
  - Does it match the referenced plan section?
  - Are SOLID principles respected?
  - Are tests meaningful (not just coverage padding)?
  - Are commit messages useful?

### 4.4 Merge Strategy

- **Squash merge** for `feat/*` branches with multiple commits —
  yields one clean commit on `develop` while preserving branch
  history in the PR.
- **Merge commit** for releases into `main`.
- **Rebase** individual commits onto `develop` when commits are
  already atomic and meaningful (rare).

---

## 5. Branch Protection Rules

Apply on **every** protected branch (`main`, `develop`,
`dev-frontend`, `dev-backend`):

### 5.0 Universal Rule: No Direct Push, No Direct Merge

**Nothing reaches a protected branch without a PR.** This is enforced
both socially and via branch protection rules below.

- ❌ No `git push` directly to `main`, `develop`, `dev-frontend`,
  `dev-backend`.
- ❌ No `git merge` on the CLI into these branches bypassing the PR
  flow (even with `--ff-only`).
- ❌ No `gh repo merge` direct-to-branch.
- ✅ Every change goes: branch → commit → push → PR → CI → review →
  squash-merge via `gh pr merge --squash`.

### 5.1 `main`

``` text
☑ Require pull request before merging
☑ Require approvals: 2
☑ Dismiss stale pull request approvals when new commits are pushed
☑ Require review from Code Owners
☑ Require status checks to pass before merging
   ☑ lint
   ☑ typecheck
   ☑ test
   ☑ migration-verify
   ☑ build
☑ Require branches to be up to date before merging
☑ Require linear history (no merge commits from PRs)
☑ Include administrators
☐ Allow force pushes          (NEVER)
☐ Allow deletions             (NEVER)
☐ Allow direct pushes         (NEVER — no exceptions)
```

### 5.2 `develop`, `dev-frontend`, `dev-backend`

``` text
☑ Require pull request before merging
☑ Require approvals: 1
☑ Require status checks to pass before merging
   ☑ lint
   ☑ typecheck
   ☑ test
   ☑ migration-verify
☑ Require branches to be up to date before merging
☑ Require linear history
☐ Allow force pushes          (NEVER)
☐ Allow deletions             (NEVER)
☐ Allow direct pushes         (NEVER — no exceptions)
```

**Recommended:** set the same rules on `dev-frontend` and
`dev-backend` so even the integration branches require PR + review.
Feature branches (`feat/*`, `fix/*`, etc.) have no protection — they
are scratch branches.

---

## 6. Pre-commit Hooks (Local Enforcement)

Use **lefthook** (`lefthook.yml`):

```yaml
pre-commit:
  parallel: true
  commands:
    backend-lint:
      glob: "src/**/*.py"
      run: cd backend && ruff check {staged_files} && ruff format --check {staged_files}
    backend-typecheck:
      glob: "src/**/*.py"
      run: cd backend && mypy src/
    frontend-lint:
      glob: "*.{ts,tsx,js,jsx}"
      run: cd frontend && eslint {staged_files}
    frontend-typecheck:
      glob: "*.{ts,tsx}"
      run: cd frontend && tsc --noEmit
    frontend-test-related:
      glob: "frontend/**/*.{ts,tsx}"
      run: cd frontend && pnpm vitest related --run
    trailing-whitespace:
      run: git diff --check
    secrets-scan:
      run: gitleaks protect --staged --no-banner

commit-msg:
  commands:
    commitlint:
      run: npx commitlint --edit $1
```

### Commitlint Config (`commitlint.config.js`)

```js
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat', 'fix', 'refactor', 'perf',
        'test', 'docs', 'chore', 'ci', 'build',
        'style', 'revert'
      ],
    ],
    'scope-enum': [
      2,
      'always',
      [
        'auth', 'users', 'algorithms', 'data-structures',
        'problems', 'progress', 'dashboard', 'roadmap',
        'visualization', 'engine', 'adapters', 'player',
        'shell', 'api', 'db', 'seed', 'migration', 'infra',
      ],
    ],
    'subject-case': [2, 'always', 'lower-case'],
    'header-max-length': [2, 'always', 72],
  },
};
```

---

## 7. CI Pipeline

Place at `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  pull_request:
    branches: [develop, main]
  push:
    branches: [develop, main]

jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: algovision
          POSTGRES_PASSWORD: test
          POSTGRES_DB: algovision_test
        ports: ['5432:5432']
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - name: Lint
        run: ruff check . && ruff format --check .
      - name: Typecheck
        run: mypy src/
      - name: Migration verify
        env:
          DATABASE_URL: postgresql+asyncpg://algovision:test@localhost:5432/algovision_test
        run: |
          alembic upgrade head
          alembic downgrade -1
          alembic upgrade head
      - name: Test
        env:
          DATABASE_URL: postgresql+asyncpg://algovision:test@localhost:5432/algovision_test
        run: pytest --cov=src --cov-fail-under=80

  frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'pnpm' }
      - run: pnpm install --frozen-lockfile
      - name: Lint
        run: pnpm lint
      - name: Typecheck
        run: pnpm typecheck
      - name: Test
        run: pnpm test -- --run --coverage
      - name: Build
        run: pnpm build
```

---

## 8. Commit Checklist (Per Commit)

Before `git commit`:

``` text
□ Subject follows format: <type>(<scope>): <summary>
□ Subject ≤ 72 chars, lowercase, no period
□ Body explains WHY (not WHAT) and references plan section
□ Code compiles / lints clean
□ Tests added if logic was added
□ No unrelated changes included
□ No secrets in diff
□ No commented-out code (delete it)
□ No debug prints / console.log
```

---

## 9. Branch Lifecycle Checklist

When starting a branch:

``` text
□ Branched from latest develop
□ Named correctly: <type>/<scope>/<description>
□ Linked to issue/ticket (e.g., "Closes #42")
```

When opening a PR:

``` text
□ Self-reviewed the diff
□ PR title matches first commit subject
□ PR template filled out completely
□ Plan section referenced
□ Test plan executed locally
□ CI green on branch
```

When merging:

``` text
□ CI green on PR
□ Required approvals obtained
□ Branch protection rules satisfied
□ Squash-merged (or rebased) into develop
□ Branch deleted on remote
□ Local branch cleaned up
```

---

## 10. Release Process

``` text
1. Cut release branch:  git checkout develop && git pull
                         git checkout -b release/v0.1.0

2. Bump version:        edit pyproject.toml, package.json
                         update CHANGELOG.md
                         commit: chore(release): bump to v0.1.0

3. Smoke test:          run E2E suite, manual smoke

4. Tag and merge:
                         git tag -a v0.1.0 -m "v0.1.0"
                         git push origin release/v0.1.0
                         open PR release/v0.1.0 → main
                         merge with merge commit (not squash)
                         git checkout develop
                         git merge --no-ff main
                         git push origin develop

5. Deploy:              trigger deploy workflow from main tag
```

---

## 11. CHANGELOG

Maintain `CHANGELOG.md` updated **per release** (not per commit —
Conventional Commits generate it):

``` markdown
# Changelog

## [0.1.0] - 2026-XX-XX

### Features
- auth: implement register and login endpoints (Argon2id)
- algorithms: list endpoint with category/difficulty filters
- visualization: array adapter and bubble sort module

### Bug Fixes
- dashboard: correct streak calculation across midnight UTC

### Refactors
- backend: split DashboardService into focused calculators

### Performance
- dashboard: add composite index on user_algorithm_progress(user_id)
```

Use `standard-version` or `release-please` to auto-generate from
Conventional Commits.

---

## 12. File Size Rule (400 Lines Max)

**Every source file must be ≤ 400 lines, including blank lines and
comments.** This is a **strict** rule. If a file approaches 400 lines,
you must split it before merging.

### 12.1 Rationale

- Files > 400 lines are a strong signal that a class or module has
  more than one responsibility.
- Long files are harder to read, review, and navigate.
- They usually indicate SRP violation (God class, god module).
- Smaller files are easier to test in isolation.
- This rule is consistent with the SOLID principles enforced
  throughout the project.

### 12.2 Scope

Applies to:

``` text
✓ *.py          (backend)
✓ *.ts / *.tsx  (frontend)
✓ *.js / *.jsx  (frontend, if any)
```

Does **not** apply to:

``` text
✗ Markdown documentation (*.md)
✗ Migration files (Alembic auto-generated structure)
✗ Generated files (Alembic env.py, Next.js scaffolding)
✗ SVG design references
✗ Lock files (pnpm-lock.yaml, poetry.lock)
```

### 12.3 Soft Warning Threshold

``` text
> 350 lines  →  YELLOW  — refactor in this commit or open a follow-up
> 400 lines  →  RED    — pre-commit hook blocks; CI fails
```

### 12.4 How to Split

Common patterns for splitting:

**Python (backend):**

``` text
# Before: 500-line service.py
service.py

# After: split by responsibility
service/
├── __init__.py
├── orchestrator.py            # main service class
├── validators.py              # input validation
├── transformers.py            # entity → DTO conversion
└── queries.py                 # complex query helpers
```

**TypeScript (frontend):**

``` text
# Before: 450-line component file
visualization-page.tsx

# After: split by concern
visualization-page/
├── index.tsx                  # main export
├── visualization-page.tsx     # composition
├── use-visualization-page.ts  # page-specific hook
├── components/
│   ├── shell.tsx
│   ├── header.tsx
│   └── sidebar.tsx
└── types.ts
```

### 12.5 Enforcement

**Pre-commit hook** (added to `lefthook.yml`):

```yaml
pre-commit:
  commands:
    file-size-check:
      run: |
        MAX=400
        FAIL=0
        for f in $(git diff --cached --name-only --diff-filter=ACMR \
                   | grep -E '\.(py|ts|tsx|js|jsx)$'); do
          if [ -f "$f" ]; then
            LINES=$(wc -l < "$f")
            if [ "$LINES" -gt "$MAX" ]; then
              echo "❌ $f: $LINES lines (max $MAX)"
              FAIL=1
            fi
          fi
        done
        exit $FAIL
```

**CI job** (`.github/workflows/ci.yml`):

```yaml
- name: Check file size
  run: |
    MAX=400
    FAIL=0
    for f in $(find . -type f \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" \) \
               -not -path "*/node_modules/*" -not -path "*/.next/*" \
               -not -path "*/__pycache__/*" -not -path "./migrations/*"); do
      LINES=$(wc -l < "$f")
      if [ "$LINES" -gt "$MAX" ]; then
        echo "::error file=$f:: $LINES lines (max $MAX)"
        FAIL=1
      fi
    done
    exit $FAIL
```

### 12.6 Exceptions

A file may legitimately exceed 400 lines **only** if:

1.  It is auto-generated (migrations, schemas, etc.).
2.  It is a large flat data structure (e.g., a constants file with
    200 small entries) — and even then, prefer a generated JSON/YAML
    file loaded at runtime.
3.  The user explicitly approves an exception in the PR description.

**Exceptions must be justified in the PR body** with:

``` text
## File Size Exception

- File: `src/modules/algorithms/service.py` (487 lines)
- Reason: Generated from OpenAPI spec; cannot split without breaking
  schema ↔ service round-trip.
- Alternative considered: ❌ Would require schema duplication.
- Approved by: @<user>
```

### 12.7 Refactoring Trigger

When you find yourself wanting to add the 401st line to a file:

1.  **Stop.**
2.  Ask: what is the new responsibility being added?
3.  Extract it into a sibling module / sibling file.
4.  Update imports.
5.  Verify all tests still pass.
6.  Commit the split as its own commit before the feature commit.

### 12.8 Per-Session Check

After each code-writing iteration, run:

``` bash
# Find files > 350 lines (warning)
find . -type f \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" \) \
  -not -path "*/node_modules/*" -not -path "*/.next/*" \
  -not -path "*/__pycache__/*" -not -path "./migrations/*" \
  -exec wc -l {} + | awk '$1 > 350' | sort -rn

# Find files > 400 lines (block)
find . -type f \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" \) \
  -not -path "*/node_modules/*" -not -path "*/.next/*" \
  -not -path "*/__pycache__/*" -not -path "./migrations/*" \
  -exec wc -l {} + | awk '$1 > 400' | sort -rn
```

Zero output = pass.

---

## 13. References

- Architecture: `ARCHITECTURE.md`
- Backend plan: `ALGOVISION_BACKEND_PLAN.md`
- Frontend plan: `ALGOVISION_FRONTEND_PLAN.md`
- Database design: `DATABASE_DESIGN.md`