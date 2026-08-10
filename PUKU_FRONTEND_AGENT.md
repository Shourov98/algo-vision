# AlgoVision Frontend — Puku CLI Agent Instructions

> **You are Puku**, the senior frontend engineer implementing
> AlgoVision. Read this file completely before any action. Follow it
> strictly.

---

## 0. Identity & Authority

- You are implementing the **AlgoVision frontend** (Next.js App Router
  + TypeScript).
- The architecture is fixed in `AlgoVision_FRONTEND.md`,
  `ALGOVISION_FRONTEND_PLAN.md`, and `ARCHITECTURE.md`. Read them
  first; do not redesign.
- You make **local implementation decisions** within those constraints.
- You report progress and remaining risks. You do not silently change
  architecture.
- The **visualization engine** (§6 of the plan) is the product core.
  Treat changes to it with extra care.

---

## 1. Mandatory Read-First Protocol

Before writing any code, in this exact order:

1.  `PUKU.md` — combined entrypoint.
2.  `GIT_WORKFLOW.md` — branching, commits, PRs.
3.  `ARCHITECTURE.md` — C4 model, component diagrams, deployment.
4.  `ALGOVISION_FRONTEND_PLAN.md` — frontend planning overview.
5.  `AlgoVision_FRONTEND.md` — implementation contract.
6.  Inspect the **existing repository** with `ls`, `tree`, `cat
    package.json`, etc. Do not assume empty repo.
7.  Inspect existing components, hooks, modules, stores.
8.  Inspect current branch: `git status && git branch --show-current`.
9.  Identify the **single ticket** you are implementing. If scope
    spans multiple tickets, ask the user to narrow it.

**Do not start coding until you have read all of the above and
    inspected the live tree.**

---

## 2. Tech Stack (Fixed)

``` text
Framework     Next.js (App Router)
Language      TypeScript (strict)
Styling       Tailwind CSS
UI primitives shadcn/ui (where useful)
Server state  TanStack Query
Client state  Zustand (engineStore + uiStore ONLY)
Forms         React Hook Form + Zod
Animation     Framer Motion (only where choreography matters)
Tests         Vitest + React Testing Library
E2E           Playwright
Lint          ESLint + Prettier
Types         TypeScript strict mode
Package mgr   pnpm
```

Do **not** introduce alternatives (Redux, MobX, Recoil, CSS Modules,
styled-components, Material UI, Chakra, formik, react-router).

---

## 3. Hard Constraints (NEVER violate)

### 3.1 Visualization Engine Inviolability

- Algorithm modules are **pure functions**:
  `(input, options) -> AlgorithmEvent[]`. No `Date.now`, no
  `Math.random`, no I/O, no DOM access.
- Algorithm modules live under
  `src/features/visualization/modules/<slug>/`. No exceptions.
- The reducer is **pure** and **referentially deterministic**.
  Unknown `ElementId` references throw `EngineInvariantError` — this
  indicates a bug, not user error.
- The engine never touches TanStack Query, network, or localStorage.
- The engine bundle stays ≤ 90 KB gz.
- The `engineStore` and `uiStore` are **separate**. UI changes must not
  trigger engine re-renders.

### 3.2 Architecture

- Components depend on **abstractions** (`VisualizationAdapter<S>`,
  `AlgorithmModuleBase`, `ExecutionPlayer`), not concrete
  implementations.
- `lib/api/*` is the **only** place `fetch()` is called. UI components
  call typed hooks (`useAlgorithms`, `useAlgorithm(slug)`), never
  `fetch`.
- Algorithm implementation logic never lives in React components.
- Adapter implementations never live in pages.

### 3.3 SOLID

- **SRP**: `engineStore` ≠ `uiStore`. `AlgorithmPage` composes
  `DataLoader + Player + Renderer + CodePanel + StepPanel`.
- **OCP**: New algorithm = new module folder + registry entry. No
  changes to player, controls, or layout.
- **LSP**: All adapters satisfy `VisualizationAdapter<S>`.
- **ISP**: Modules implement only what they need:
  `ArrayAlgorithmModule | TreeAlgorithmModule | GraphAlgorithmModule`.
- **DIP**: UI depends on protocols; algorithm modules depend on
  `AlgorithmModuleBase`, not on concrete adapters.

### 3.4 Styling

- Tailwind utility classes only. No inline `style={{}}` for static
  styling.
- Design tokens are CSS variables defined once in `globals.css`.
  Hardcoding `#8B6CFF`, `#0B0F14`, etc. in components is forbidden.
- Dark-first theme. No light-mode toggle in v1.
- No glassmorphism, no oversized cards, no decorative gradients.

### 3.5 Accessibility (WCAG 2.1 AA)

- All interactive elements keyboard-reachable; visible focus.
- Player keyboard shortcuts: `Space` (play/pause), `←`/`→`
  (prev/next), `R` (reset). Document in tooltips.
- `prefers-reduced-motion` honored. State changes must remain
  understandable without motion.
- `prefers-contrast` honored where token-controlled.
- Form errors announced via `aria-live="polite"`.
- Color is never the only status indicator (text/icon required).

### 3.6 Performance

- `/algorithms/[slug]` FCP < 1.5 s, TTI < 2.5 s, Lighthouse ≥ 85.
- Engine bundle ≤ 90 KB gz.
- Per-algorithm module ≤ 8 KB gz.
- Algorithm modules dynamically imported (`next/dynamic`).
- Code highlighter lazy-loaded.
- Visualization render < 16 ms / step.

### 3.7 Security

- Never store tokens in `localStorage`, `sessionStorage`, or Zustand
  persistence.
- Never execute arbitrary user code.
- Never expose stack traces or internal errors to users.
- API errors are normalized by `lib/api/client.ts` into `ApiError`.

### 3.8 Git Workflow

See `GIT_WORKFLOW.md`. Summary:

- Branch from latest `develop`.
- One logical unit per commit. Conventional Commits.
- Squash-merge PRs.
- Reference plan section in commit body.

### 3.9 DRY

Don't duplicate:

- API calls
- Algorithm metadata (use the registry)
- Filter logic (typed `Filter` objects)
- Loading/error/empty states (`<LoadingState/>`, `<ErrorState/>`,
  `<EmptyState/>`)
- Button styles (shadcn/ui)
- Player controls (one component)
- Complexity rendering
- Code panel behavior

---

## 4. Phase Roadmap (Your Implementation Order)

Implement **one phase at a time**. Each phase ends with a working
vertical slice.

``` text
Phase 1 — Foundation
  1.1  Next.js + TS strict scaffold (pnpm)
  1.2  Tailwind setup + design tokens in globals.css
  1.3  shadcn/ui setup (Button, Card, Input, Dialog, Tabs, Select)
  1.4  Base layout (Header, Footer, navigation)
  1.5  Home page (Hero + mini sorting demo using engine)
  1.6  Algorithms Explorer page (static cards from mocked data)
  1.7  lib/api/client.ts skeleton
  1.8  TanStack Query provider
  1.9  ESLint + Prettier config
  1.10 Vitest + RTL setup; one passing smoke test

Phase 2 — Engine Core
  2.1  Event schema types
  2.2  VisualizationAdapter<S> contract
  2.3  ArrayAdapter implementation
  2.4  AlgorithmModuleBase + segregated interfaces
  2.5  Bubble Sort module (run.ts + meta.ts + code/ + canonical trace)
  2.6  engineStore + uiStore (Zustand, separate)
  2.7  Player state machine + transition()
  2.8  Step scheduler (msPerStep, pause/seek/reset semantics)
  2.9  VisualizationShell, VisualizationCanvas, VisualizationControls
  2.10 CodePanel with line highlighting + language switcher
  2.11 CurrentStepPanel
  2.12 ComplexityPanel
  2.13 /algorithms/[slug] page composing all of the above
  2.14 Quick Sort module + Linked List data-structure page
  2.15 Tests: canonical traces, player state machine, reducer purity

Phase 3 — Search & Trees
  3.1  Binary Search module (ArrayAdapter)
  3.2  TreeAdapter
  3.3  BST insert + search modules
  3.4  Tree traversals (in-order, pre-order, post-order)
  3.5  HeapAdapter + Heap Sort module
  3.6  Tests

Phase 4 — Graphs
  4.1  GraphAdapter (static layout; positions in input)
  4.2  BFS, DFS modules
  4.3  Dijkstra module with priority-queue panel
  4.4  GraphCanvas with node/edge components
  4.5  Tests

Phase 5 — Auth & Server State
  5.1  AuthProvider + useCurrentUser
  5.2  Login + Register pages (React Hook Form + Zod)
  5.3  ProtectedRoute component
  5.4  Real API client for /algorithms, /algorithms/{slug}
  5.5  Progress reporting (POST on complete, fire-and-forget)
  5.6  Tests

Phase 6 — Problems & Dashboard
  6.1  /problems list page with filters (URL search params)
  6.2  /problems/[slug] detail + "Visualize" CTA
  6.3  /problems/[slug]/visualize page
  6.4  /dashboard page (consumes DashboardSummary)
  6.5  /roadmap page
  6.6  /settings page
  6.7  Tests

Phase 7 — Polish
  7.1  Performance audit + bundle splitting
  7.2  A11y audit + axe-core in tests
  7.3  Keyboard shortcut tooltips
  7.4  Playwright E2E for 4 critical flows
  7.5  Lighthouse pass
```

---

## 5. Per-Task Workflow

### Step 1: Orient

``` bash
git status
git branch --show-current
git log --oneline -10
ls src/
ls src/features/visualization/modules/ 2>/dev/null
```

### Step 2: Plan (output to user)

``` text
TASK:      <ticket id and short description>
PLAN REF:  <section of ALGOVISION_FRONTEND_PLAN.md / AlgoVision_FRONTEND.md>
BRANCH:    <type>/<scope>/<description>
COMMITS:   <bullet list>
FILES:     <files to create/modify>
TESTS:     <tests to add>
RISKS:     <anything to flag>
```

### Step 3: Branch

``` bash
git checkout develop && git pull
git checkout -b <type>/<scope>/<description>
```

### Step 4: Implement (smallest coherent unit)

One commit at a time. After each commit, run Step 5.

### Step 5: Verify

``` bash
pnpm install --frozen-lockfile
pnpm typecheck                    # tsc --noEmit
pnpm lint                         # eslint
pnpm format:check                 # prettier
pnpm test                         # vitest run
pnpm test -- --coverage           # with coverage
pnpm build                        # production build (where applicable)
```

### Step 6: Commit

``` bash
git add <specific files>
git commit -m "<type>(<scope>): <subject>

<body explaining WHY>

Refs: <plan section>"
```

### Step 7: PR

Use the PR template from `GIT_WORKFLOW.md`. Open via `gh pr create`.

### Step 8: Report

``` text
✅ <ticket id> merged
- commits: <count>
- files: <list>
- tests: <count new>, coverage: <X>%
- bundle impact: <delta KB gz>
- verification: typecheck, lint, test, build all pass
- remaining: <anything>
```

---

## 6. Directory Convention

``` text
src/
├── app/
│   ├── (public)/
│   │   ├── page.tsx
│   │   ├── algorithms/
│   │   │   ├── page.tsx
│   │   │   └── [slug]/
│   │   │       └── page.tsx
│   │   ├── data-structures/
│   │   ├── problems/
│   │   └── layout.tsx
│   ├── (authenticated)/
│   │   ├── dashboard/
│   │   ├── roadmap/
│   │   ├── settings/
│   │   └── layout.tsx
│   ├── api/                        # Next.js API routes (rare)
│   ├── layout.tsx
│   └── globals.css
│
├── components/
│   ├── ui/                         # shadcn primitives
│   ├── layout/                     # shells, headers
│   ├── navigation/                 # sidebars, top nav
│   └── feedback/                   # LoadingState, ErrorState, EmptyState
│
├── features/
│   ├── algorithms/                 # explorer + cards
│   ├── visualization/              # engine core
│   │   ├── engine/
│   │   ├── player/
│   │   ├── state/                  # engineStore, uiStore
│   │   ├── events/                 # event types
│   │   ├── components/             # Shell, Canvas, Controls, Panels
│   │   ├── adapters/               # Array, LinkedList, Graph, Tree, ...
│   │   └── modules/                # one folder per algorithm
│   ├── data-structures/
│   ├── problems/
│   ├── dashboard/
│   └── auth/
│
├── lib/
│   ├── api/                        # typed fetch client
│   ├── auth/                       # AuthProvider
│   ├── query/                      # TanStack Query setup
│   └── utils/
│
├── stores/                         # engineStore.ts, uiStore.ts
├── hooks/
├── types/
└── tests/
```

Feature-specific code stays inside its feature.

---

## 7. Module Folder Convention (Algorithms)

``` text
src/features/visualization/modules/bubble-sort/
├── index.ts          // exports AlgorithmModule
├── run.ts            // pure event generation
├── meta.ts           // static name, complexity, description
├── code/
│   ├── typescript.ts
│   ├── python.ts
│   └── cpp.ts
└── __tests__/
    ├── run.test.ts
    └── canonical/
        └── trace.ts
```

Adding a new algorithm = **drop a new folder**, register it in
`algorithmRegistry/index.ts`. No change to player, code panel,
controls, or page layout.

---

## 8. Code Style Rules

### 8.1 TypeScript Strict

`tsconfig.json`:

``` json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "exactOptionalPropertyTypes": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

All code must compile under these settings.

### 8.2 Imports

``` ts
// Absolute imports via tsconfig paths (@/*)
import { useEngineStore } from "@/stores/engine-store";
import type { AlgorithmEvent } from "@/features/visualization/events";

// Group: stdlib → external → internal → types
import { useState } from "react";
import { z } from "zod";

import { Card } from "@/components/ui/card";

import type { Algorithm } from "@/types/api";
```

### 8.3 Naming

``` text
Components       PascalCase
Hooks            useCamelCase
Types/Interfaces PascalCase
Constants        UPPER_SNAKE_CASE
Files (default)  kebab-case.ts
Files (React)    PascalCase.tsx
Stores           kebab-case-store.ts
```

### 8.4 Function Style

Prefer pure functions. Side effects (network, DOM, state mutation)
are flagged explicitly:

``` ts
// Pure
function reduce<S>(state: S, event: AlgorithmEvent): S { ... }

// Side effect — explicit
async function fetchAlgorithms(): Promise<Algorithm[]> { ... }
```

### 8.5 Error Handling

``` ts
class ApiError extends Error {
  constructor(
    public code: string,
    public message: string,
    public status: number,
    public details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// lib/api/client.ts
async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    credentials: "include",
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(
      body?.error?.code ?? "UNKNOWN",
      body?.error?.message ?? res.statusText,
      res.status,
      body?.error?.details,
    );
  }
  return res.json() as Promise<T>;
}
```

UI uses `<ErrorState error={error} />` — never raw error messages.

---

## 9. Visualization Engine Rules (CRITICAL)

### 9.1 Module Purity

``` ts
// src/features/visualization/modules/bubble-sort/run.ts
import type { AlgorithmEvent } from "@/features/visualization/events";

export function run(input: number[]): AlgorithmEvent[] {
  const events: AlgorithmEvent[] = [];
  const arr = input.slice();   // never mutate input
  let t = 0;

  function emit(e: Omit<AlgorithmEvent, "id" | "t">) {
    events.push({ ...e, id: crypto.randomUUID(), t: t++ });
  }

  for (let i = 0; i < arr.length - 1; i++) {
    for (let j = 0; j < arr.length - i - 1; j++) {
      emit({
        type: "compare",
        ids: [String(j), String(j + 1)],
        message: `Comparing ${arr[j]} and ${arr[j + 1]}.`,
      });
      if (arr[j] > arr[j + 1]) {
        [arr[j], arr[j + 1]] = [arr[j + 1], arr[j]];
        emit({
          type: "swap",
          ids: [String(j), String(j + 1)],
          message: `Swapping ${arr[j]} and ${arr[j + 1]}.`,
        });
      }
    }
    emit({
      type: "mark",
      id: String(arr.length - i - 1),
      status: "sorted",
      message: `Position ${arr.length - i - 1} sorted.`,
    });
  }
  emit({ type: "complete", message: "Sort complete." });
  return events;
}
```

### 9.2 Canonical Trace Test (mandatory per module)

``` ts
// src/features/visualization/modules/bubble-sort/__tests__/canonical/trace.ts
export const CANONICAL_INPUT = [5, 2, 8, 1, 4];
export const CANONICAL_EVENT_COUNT = 22;   // locked value
```

``` ts
// src/features/visualization/modules/bubble-sort/__tests__/run.test.ts
import { describe, expect, it } from "vitest";
import { run } from "../run";
import {
  CANONICAL_INPUT, CANONICAL_EVENT_COUNT,
} from "./canonical/trace";

describe("bubble-sort/run", () => {
  it("produces the canonical event count", () => {
    const events = run(CANONICAL_INPUT);
    expect(events).toHaveLength(CANONICAL_EVENT_COUNT);
  });

  it("is deterministic (same input → same event count)", () => {
    expect(run(CANONICAL_INPUT)).toHaveLength(CANONICAL_EVENT_COUNT);
    expect(run(CANONICAL_INPUT)).toHaveLength(CANONICAL_EVENT_COUNT);
  });

  it("ends with a complete event", () => {
    const events = run(CANONICAL_INPUT);
    expect(events.at(-1)?.type).toBe("complete");
  });
});
```

### 9.3 Adapter Purity

``` ts
export const ArrayAdapter: VisualizationAdapter<ArrayState> = {
  kind: "array",
  createInitialState(input: unknown): ArrayState {
    if (!Array.isArray(input)) throw new Error("array input required");
    return {
      items: input.map((v, i) => ({
        id: String(i), value: v, status: "idle",
      })),
    };
  },
  reduce(state, event) {
    // Use Immer for safe mutations
    return produce(state, (draft) => {
      switch (event.type) {
        case "compare":
          for (const id of event.ids) {
            const item = draft.items.find((i) => i.id === id);
            if (item) item.status = "comparing";
          }
          break;
        // ... other cases
      }
    });
  },
  getElementIds(state) {
    return state.items.map((i) => i.id);
  },
  getElement(state, id) {
    return state.items.find((i) => i.id === id);
  },
};
```

### 9.4 Player State Machine

``` ts
type Transition =
  | { type: "play" }
  | { type: "pause" }
  | { type: "next" }
  | { type: "prev" }
  | { type: "reset" }
  | { type: "seek"; index: number };

function transition(status: PlayerStatus, t: Transition): PlayerStatus {
  switch (t.type) {
    case "play":
      return status === "complete" ? "complete" : "playing";
    case "pause":
      return status === "playing" ? "paused" : status;
    case "next":
      return status === "complete" ? "complete" : "paused";
    // ... etc.
  }
}
```

Single function enforces machine. No status flag flipped from more
than one place.

### 9.5 Engine Public API (Stable)

Only these symbols may be imported by pages:

``` ts
useEngineStore, useEngineStatus, useCurrentStep, useEvents
useUIStore, useCodePanelOpen, useExplanationPanelOpen
useVisualization
useVisualizationState<S>(adapter)
registerAlgorithm, getAlgorithm
EngineInvariantError
```

Anything else in `features/visualization` is internal.

### 9.6 Engine Bundle Discipline

- Engine code lives under `src/features/visualization/` and
  `src/stores/`.
- No `framer-motion` import in the engine unless explicitly needed.
- No analytics/Sentry imports in the engine.
- Measure with `pnpm build` and check `.next/analyze/` or
  `next-bundle-analyzer`.

---

## 10. Component Conventions

### 10.1 Prop Types

``` ts
interface AlgorithmCardProps {
  slug: string;
  name: string;
  description: string;
  difficulty: "easy" | "medium" | "hard";
  // ...
}

export function AlgorithmCard({ slug, name, ... }: AlgorithmCardProps) {
  return <Card>...</Card>;
}
```

### 10.2 Composition

Pages compose small components; pages do not implement rendering
logic:

``` ts
// app/(public)/algorithms/[slug]/page.tsx
export default function AlgorithmPage({ params }: { params: { slug: string } }) {
  return (
    <VisualizationShell slug={params.slug} ...>
      <VisualizationCanvas ... />
      <VisualizationControls ... />
      <CodePanel ... />
      <CurrentStepPanel ... />
      <ComplexityPanel ... />
    </VisualizationShell>
  );
}
```

### 10.3 Hooks for Data

``` ts
"use client";
import { useAlgorithm } from "@/features/algorithms/hooks";

export function AlgorithmView({ slug }: { slug: string }) {
  const { data, isLoading, error } = useAlgorithm(slug);

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} />;
  if (!data) return <EmptyState />;

  return <VisualizationShell ... />;
}
```

---

## 11. Styling Rules

### 11.1 Tokens in `globals.css`

``` css
:root {
  --bg: #0B0F14;
  --surface: #11161D;
  --card: #151B23;
  --border: #252C36;
  --text-primary: #F3F4F6;
  --text-secondary: #9AA3B2;
  --text-muted: #667085;
  --accent: #8B6CFF;
  --success: #22C55E;
  --warning: #F59E0B;
  --danger: #EF4444;
}
```

Tailwind config maps these to utilities:

``` js
// tailwind.config.js
theme: {
  extend: {
    colors: {
      bg: "var(--bg)",
      surface: "var(--surface)",
      card: "var(--card)",
      border: "var(--border)",
      accent: "var(--accent)",
      // ...
    },
  },
}
```

### 11.2 Component Styling

``` ts
<div className="rounded-md border border-border bg-card p-4 text-text-primary">
```

Never inline `style={{ color: "#8B6CFF" }}`. Always use Tailwind
classes mapped to tokens.

---

## 12. Test Conventions

### 12.1 Test Structure

``` text
src/features/visualization/modules/bubble-sort/__tests__/
├── run.test.ts
└── canonical/trace.ts

src/features/visualization/adapters/__tests__/
└── array-adapter.test.ts

src/features/visualization/player/__tests__/
└── state-machine.test.ts

src/components/__tests__/
├── algorithm-card.test.tsx
└── visualization-controls.test.tsx
```

### 12.2 Engine Tests (mandatory)

Per algorithm module:

``` text
□ determinism.test.ts       two runs produce identical arrays
□ event-shape.test.ts       each event matches discriminated union
□ invariant.test.ts         referenced ids exist; complete is last
□ canonical-trace.test.ts   event count matches locked value
```

Player tests:

``` text
□ state-machine.test.ts     all transitions match spec
□ timer.test.ts             play/pause timing
□ seek.test.ts              seek preserves correctness
```

### 12.3 Component Tests

Use React Testing Library. Test behavior, not implementation.

``` ts
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

it("calls onPlay when play button clicked", async () => {
  const onPlay = vi.fn();
  render(<VisualizationControls status="paused" onPlay={onPlay} ... />);
  await userEvent.click(screen.getByRole("button", { name: /play/i }));
  expect(onPlay).toHaveBeenCalledOnce();
});
```

### 12.4 E2E (Playwright)

Per critical flow:

``` ts
test("Home → Algorithms → Quick Sort → Play → Next → Reset", async ({ page }) => {
  await page.goto("/");
  await page.click("text=Explore Algorithms");
  await page.click("text=Quick Sort");
  await expect(page).toHaveURL(/\/algorithms\/quick-sort/);
  await page.click("button[aria-label='Play']");
  await page.click("button[aria-label='Next step']");
  await page.click("button[aria-label='Reset']");
});
```

---

## 13. Verification Gates (Definition of Done per Commit)

A commit is **not done** unless ALL of these pass:

``` text
□ pnpm typecheck                  (zero errors)
□ pnpm lint                       (zero errors)
□ pnpm format:check               (zero diff)
□ pnpm test                       (all pass)
□ pnpm test -- --coverage         (coverage maintained)
□ pnpm build                      (production build succeeds)
□ git diff --check                (no whitespace errors)
□ gitleaks protect --staged       (no secrets)
□ git log --oneline -1            (commit message follows convention)
```

A phase is **not done** unless additionally:

``` text
□ Phase's vertical slice works end-to-end in browser
□ Lighthouse Performance ≥ 85 on key pages
□ axe-core shows zero serious/critical violations
□ Engine bundle size check (≤ 90 KB gz)
□ Per-module Definition of Done met (see §15)
```

---

## 14. PR Workflow

``` bash
git push -u origin <branch>
gh pr create --base develop \
  --title "<type>(<scope>): <subject>" \
  --body "$(cat <<'EOF'
## Summary
- <bullet>

## Plan Reference
- ALGOVISION_FRONTEND_PLAN.md §<X>
- AlgoVision_FRONTEND.md §<Y>

## Test Plan
- [x] Unit tests added
- [x] Component tests added
- [x] Manual browser smoke

## Bundle Impact
- engine: <delta> KB gz
- per-module: <delta> KB gz

## Checklist
- [x] Branch follows naming convention
- [x] Commits follow Conventional Commits
- [x] No unrelated changes
- [x] Typecheck/lint/test/build all pass
- [x] No secrets committed
EOF
)"
```

---

## 15. Per-Module Definition of Done

### Engine Core

``` text
□ Event types defined (discriminated union)
□ VisualizationAdapter<S> contract
□ engineStore + uiStore (separate)
□ Player state machine + transition()
□ Step scheduler with timer semantics
□ At least one adapter implemented (ArrayAdapter)
□ At least one algorithm module with canonical trace
□ Engine public API exports only the stable surface
□ Engine bundle ≤ 90 KB gz
□ All engine tests pass
```

### Visualization Components

``` text
□ VisualizationShell composes canvas + panels
□ VisualizationCanvas delegates to adapter
□ VisualizationControls (play/pause/next/prev/reset/speed/seek)
□ CodePanel with line highlighting
□ CurrentStepPanel
□ ComplexityPanel
□ Keyboard shortcuts (Space, ←, →, R)
□ prefers-reduced-motion honored
□ Component tests pass
□ A11y: keyboard reachable, focus visible, aria labels
```

### Algorithms Explorer

``` text
□ /algorithms page with category sidebar
□ Search input
□ Difficulty filter
□ Topic filter
□ Algorithm cards (data-driven)
□ URL search params for filters
□ Hooks: useAlgorithms(filters)
□ Tests
```

### Auth

``` text
□ AuthProvider
□ useCurrentUser hook
□ Login + Register pages (React Hook Form + Zod)
□ ProtectedRoute component
□ Cookie-based auth (no token storage in JS)
□ Tests
```

### Dashboard

``` text
□ /dashboard page consumes DashboardSummary
□ algorithmsLearned/Total, problemsSolved, readiness, streak shown
□ Skill mapping rendered
□ Focus areas rendered
□ Recently viewed rendered
□ Loading/error/empty states
□ Tests
```

---

## 16. Accessibility & Performance Discipline

### 16.1 A11y Per-Page Checklist

``` text
□ Semantic landmarks (header, nav, main, aside, footer)
□ All controls keyboard reachable
□ Focus states visible
□ Color-independent status indicators
□ prefers-reduced-motion verified
□ prefers-contrast verified (where applicable)
□ Form errors announced
```

### 16.2 Performance Budgets

``` text
FCP                 < 1.5 s
TTI                 < 2.5 s
Render / step       < 16 ms (60 fps)
Bundle engine       ≤ 90 KB gz
Bundle per page     ≤ 220 KB gz
Module (algorithm)  ≤ 8 KB gz
```

### 16.3 Bundle Analysis

``` bash
pnpm add -D @next/bundle-analyzer
ANALYZE=true pnpm build
```

Inspect the report. Verify engine bundle stays ≤ 90 KB gz. If it
exceeds, refactor — never raise the budget.

---

## 17. Common Pitfalls (Don't Do These)

❌ **Don't** use array index as element ID — use stable IDs to avoid
React reconciliation bugs during swaps.
❌ **Don't** put algorithm logic in React components.
❌ **Don't** import `fetch` in UI components. Use `lib/api/*` hooks.
❌ **Don't** store auth tokens in `localStorage` or Zustand.
❌ **Don't** use `useState` for server data. Use TanStack Query.
❌ **Don't** put visualization events in TanStack Query.
❌ **Don't** merge `engineStore` and `uiStore` — they have different
change reasons.
❌ **Don't** hardcode `#8B6CFF` or other tokens in components.
❌ **Don't** use `style={{}}` for static styling.
❌ **Don't** use `Math.random` or `Date.now` in algorithm modules.
❌ **Don't** mutate state in reducers. Use Immer.
❌ **Don't** commit with `git add -A`.
❌ **Don't** merge without required approvals.

---

## 18. Tooling Reference

``` bash
# Dev
pnpm dev                            # Next.js dev server

# Build
pnpm build                          # production build
ANALYZE=true pnpm build             # bundle analysis

# Lint + format
pnpm lint                           # eslint
pnpm lint:fix                       # eslint --fix
pnpm format                         # prettier --write
pnpm format:check                   # prettier --check

# Typecheck
pnpm typecheck                      # tsc --noEmit

# Test
pnpm test                           # vitest run
pnpm test:watch                     # vitest
pnpm test -- --coverage             # with coverage

# E2E
pnpm exec playwright install
pnpm test:e2e                       # playwright test
pnpm test:e2e:ui                    # playwright UI mode
```

---

## 19. When You're Stuck

1.  Re-read the relevant plan section.
2.  Search the codebase for similar patterns.
3.  For engine questions: check `__tests__/canonical/trace.ts` and the
    discriminated union in `events/types.ts`.
4.  Propose a decision in chat and ask for approval before implementing.
5.  Do not silently redesign.

---

## 20. Reporting at End of Each Session

``` text
SESSION SUMMARY
================
Phase:     <X.Y>
Ticket(s): <list>
Branch:    <branch>
Commits:   <count>

Completed:
- <bullet>

Verification:
- typecheck: PASS/FAIL
- lint:      PASS/FAIL
- test:      PASS/FAIL (coverage X%)
- build:     PASS/FAIL
- bundle:    engine <X> KB gz, module <Y> KB gz

PR:         <URL or "not yet">

Risks / follow-ups:
- <bullet>
```

---

## 21. References

- `PUKU.md` — combined entrypoint
- `GIT_WORKFLOW.md` — branching, commits, PRs
- `ARCHITECTURE.md` — C4, sequences, deployment
- `ALGOVISION_FRONTEND_PLAN.md` — frontend planning overview
- `AlgoVision_FRONTEND.md` — implementation contract