# AlgoVision Frontend Plan (High-Level Roadmap)

> Companion to `AlgoVision_FRONTEND.md`. This file is the planning
> overview — architecture, modules, components, state ownership,
> performance budget, and phase roadmap. The implementation contract
> lives in `AlgoVision_FRONTEND.md`.

---

## 1. Goal

Reproduce the supplied AlgoVision designs with a reusable algorithm
**execution + visualization engine** at the core. Every page that shows
an algorithm must reuse the same engine, controls, code panel, and step
explanation. New algorithms must be addable without rewriting page or
player code.

## 2. Stack

| Concern        | Choice                                            |
|----------------|---------------------------------------------------|
| Framework      | Next.js (App Router)                              |
| Language       | TypeScript (strict)                               |
| Styling        | Tailwind CSS                                      |
| UI primitives  | shadcn/ui where useful                            |
| Server state   | TanStack Query                                    |
| Client state   | Zustand (visualization store only)                |
| Forms          | React Hook Form + Zod                             |
| Animation      | Framer Motion only where choreography matters     |
| Tests          | Vitest + React Testing Library; Playwright E2E    |
| Lint/format    | ESLint + Prettier                                 |

## 3. Visual Direction

Dark-first developer-tool UI. Design tokens (centralized as CSS vars,
never hard-coded):

``` text
Background      #0B0F14
Surface         #11161D
Card            #151B23
Border          #252C36
Primary text    #F3F4F6
Secondary text  #9AA3B2
Muted text      #667085
Accent          #8B6CFF
Success         #22C55E
Warning         #F59E0B
Danger          #EF4444
```

Typography: Inter (UI) + JetBrains Mono (code/data).

Avoid: glassmorphism, oversized cards, decorative gradients, childish
illustrations, animations unrelated to algorithm state.

## 4. Routes

``` text
/                                  Home
/algorithms                        Explorer
/algorithms/[slug]                 Algorithm page (visualization)
/data-structures                   Catalog
/data-structures/[slug]            Detail
/problems                          Interview problems list
/problems/[slug]                   Problem detail
/problems/[slug]/visualize         Visualization for a problem
/dashboard                        Authenticated
/roadmap                          Authenticated
/settings                         Authenticated
/documentation                     Static
```

Public pages do not require auth. Dashboard, roadmap, settings do.
Visualization pages are public.

## 5. Module / Folder Layout

``` text
src/
├── app/                              # Next.js App Router
│   ├── (public)/
│   │   ├── page.tsx                  # Home
│   │   ├── algorithms/
│   │   ├── data-structures/
│   │   └── problems/
│   ├── (authenticated)/
│   │   ├── dashboard/
│   │   ├── roadmap/
│   │   └── settings/
│   ├── api/                          # Next.js API routes (rare)
│   ├── layout.tsx
│   └── globals.css
│
├── components/
│   ├── ui/                           # shadcn primitives
│   ├── layout/                       # shells, headers, footers
│   ├── navigation/                   # sidebars, top nav
│   └── feedback/                     # loading/error/empty states
│
├── features/                         # feature-first, isolated
│   ├── algorithms/                   # explorer + cards
│   ├── visualization/                # engine (see §6)
│   │   ├── engine/
│   │   ├── player/
│   │   ├── state/
│   │   ├── events/
│   │   ├── components/
│   │   ├── adapters/
│   │   └── modules/                  # one folder per algorithm
│   ├── data-structures/
│   ├── problems/
│   ├── dashboard/
│   └── auth/
│
├── lib/
│   ├── api/                          # typed API client
│   ├── auth/                         # AuthProvider, hooks
│   ├── query/                        # TanStack Query setup
│   └── utils/
│
├── stores/
│   └── visualization-store.ts        # Zustand
│
├── hooks/
├── types/
└── tests/
```

Feature-specific code stays in the feature. Shared abstractions live in
`components/` or `lib/`.

## 6. Visualization Engine (Product Core)

The engine is the most important frontend module. It owns **five**
concerns only:

1.  Produce deterministic `AlgorithmEvent[]` from an algorithm module.
2.  Fold events into adapter-specific visualization state via a pure
    reducer.
3.  Expose a player: play / pause / next / prev / reset / seek / speed.
4.  Notify subscribers when current step index changes.
5.  Provide hook points for code-panel line highlighting.

### 6.1 Canonical Event Schema

``` ts
type ElementId = string;       // stable across replays
type LineNumber = number;      // 1-indexed

interface BaseEvent {
  id: string;                  // crypto.randomUUID()
  t: number;                   // monotonic step counter
  line?: LineNumber;
  message: string;
}

type AlgorithmEvent =
  | (BaseEvent & { type: "compare";  ids: ElementId[] })
  | (BaseEvent & { type: "swap";     ids: [ElementId, ElementId] })
  | (BaseEvent & { type: "visit";    id: ElementId })
  | (BaseEvent & { type: "select";   ids: ElementId[] })
  | (BaseEvent & { type: "insert";   id: ElementId; value: unknown })
  | (BaseEvent & { type: "delete";   id: ElementId })
  | (BaseEvent & { type: "update";   id: ElementId; value: unknown })
  | (BaseEvent & { type: "mark";     id: ElementId; status: MarkStatus })
  | (BaseEvent & { type: "relax";    from: ElementId; to: ElementId;
                   weight?: number })
  | (BaseEvent & { type: "found";    ids: ElementId[] })
  | (BaseEvent & { type: "enqueue";  id: ElementId })
  | (BaseEvent & { type: "dequeue";  id: ElementId })
  | (BaseEvent & { type: "push";     id: ElementId; value: unknown })
  | (BaseEvent & { type: "pop";      id: ElementId })
  | (BaseEvent & { type: "complete"; summary?: Record<string, unknown> });

type MarkStatus =
  | "idle" | "active" | "comparing" | "swapping"
  | "sorted" | "pivot" | "visited" | "frontier"
  | "current" | "target" | "found";
```

Determinism rules:

-   Event `id` generated at algorithm-run time only.
-   Event order is the playback order; engine never reorders.
-   Algorithm module is a pure function `(input, options) -> AlgorithmEvent[]`.
    No `Date.now`, no `Math.random`, no I/O.
-   Two runs with the same input produce identical event arrays.

### 6.2 Adapter Contract

``` ts
interface VisualizationAdapter<S> {
  readonly kind:
    | "array" | "linked-list" | "tree" | "graph"
    | "heap" | "dp-table" | "recursion-tree" | "stack-queue";

  createInitialState(input: unknown, seed?: ElementId[]): S;
  reduce(state: S, event: AlgorithmEvent): S;            // pure
  getElementIds(state: S): ElementId[];
  getElement(state: S, id: ElementId): ElementView | undefined;
}

interface ElementView {
  id: ElementId;
  label?: string;
  value?: unknown;
  status: MarkStatus;
  meta?: Record<string, unknown>;
```

Concrete adapters: `ArrayAdapter`, `LinkedListAdapter`, `TreeAdapter`,
`GraphAdapter`, `HeapAdapter`, `DpTableAdapter`, `RecursionTreeAdapter`,
`StackQueueAdapter`. All implement the same contract.

Reducer discipline:

-   Pure; never mutate input state.
-   Use Immer or structuredClone.
-   Throw `EngineInvariantError` for unknown `ElementId` references.

### 6.3 Player State Machine

``` ts
type PlayerStatus =
  | "idle"       // events generated, not yet stepped into
  | "playing"    // auto-advancing
  | "paused"     // stopped at currentStep
  | "seeking"    // user scrubbing (transient)
  | "complete";  // currentStep === events.length - 1
```

Transitions:

``` text
idle     --play()-->       playing
playing  --pause()-->      paused
playing  --stepEnd-->      complete (last event)
paused   --play()-->       playing
paused   --next()-->       paused | complete
paused   --prev()-->       paused | idle
idle     --next()-->       paused
any      --reset()-->      idle
any      --seek(i)-->      paused (or playing if was playing)
```

Single `transition()` function enforces the machine. No status flag
flipped from more than one place.

### 6.4 Step Advancement

-   Speed: `msPerStep` ∈ {400, 250, 150, 80, 40, 15}; default 150.
-   One `setTimeout`-based scheduler. `requestAnimationFrame` may be
    used for rendering smoothness only — never for advancement.
-   `pause` cancels pending timer.
-   `seek` cancels timer; does not auto-resume unless prior state was
    `playing`.

### 6.5 Algorithm Module Contract (SOLID: Interface Segregation)

A single fat `AlgorithmModule` interface forces every module to
implement methods it does not need (graph algorithms don't need
`defaultInput()` for arrays; tree algorithms need a `root` builder).
We segregate into a base interface plus kind-specific extensions.

``` ts
// Every module implements this
interface AlgorithmModuleBase {
  slug: string;                                    // matches backend slug
  visualizationKind: VisualizationAdapter<unknown>["kind"];
  meta: AlgorithmMeta;                             // static name, complexity
  run(input: unknown, options?: RunOptions): AlgorithmEvent[];
}

interface AlgorithmMeta {
  name: string;
  description: string;
  difficulty: "easy" | "medium" | "hard";
  complexity?: {
    best?: string;
    average?: string;
    worst?: string;
    space?: string;
  };
  topics: string[];
}

// Segregated input contracts — modules implement only what they need
interface HasDefaultInput<I> {
  defaultInput: () => I;
}

interface HasRootInput {
  defaultRoot: () => TreeNode | null;
}

interface HasGraphInput {
  defaultGraph: () => { nodes: GraphNode[]; edges: GraphEdge[] };
}

// Real modules compose only the interfaces they need
type ArrayAlgorithmModule<I = number[]> =
  AlgorithmModuleBase & HasDefaultInput<I>;

type TreeAlgorithmModule =
  AlgorithmModuleBase & HasRootInput;

type GraphAlgorithmModule =
  AlgorithmModuleBase & HasGraphInput;

type AlgorithmModule =
  ArrayAlgorithmModule | TreeAlgorithmModule | GraphAlgorithmModule;

interface RunOptions {
  seed?: number;             // reserved
  highlightLines?: boolean;
}
```

**Type guards** discriminate the kind at the consumer site:

``` ts
function isArrayModule(m: AlgorithmModule): m is ArrayAlgorithmModule {
  return (m as ArrayAlgorithmModule).defaultInput !== undefined;
}
```

This means:

- Bubble Sort implements `ArrayAlgorithmModule<number[]>` and nothing
  else.
- Dijkstra implements `GraphAlgorithmModule` and nothing else.
- The player/engine only depend on `AlgorithmModuleBase`.

### 6.6 Module Folder Convention

``` text
src/features/visualization/modules/
  bubble-sort/
    index.ts          // exports AlgorithmModule
    run.ts            // pure event generation
    code/
      typescript.ts   // educational source
      python.ts
      cpp.ts
    meta.ts           // static name, complexity, description
    __tests__/
      run.test.ts
      canonical/trace.ts    // canonical event trace
```

Adding a new algorithm = drop a new folder, register in
`algorithmRegistry/index.ts`. No change to player, controls, code
panel, page layout.

### 6.7 Animation Choreography

| Event     | Effect                                                 |
|-----------|--------------------------------------------------------|
| compare   | both elements pulse accent border (~120 ms)            |
| swap      | elements translate to each other's positions           |
| visit     | node fills `visiting`, settles to `visited`            |
| select    | elements get `pivot` ring; previous pivot → `idle`     |
| insert    | new element fades in at target slot                    |
| delete    | element fades out, layout collapses                    |
| mark      | element transitions to new status (CSS)                |
| relax     | edge thickness pulses; destination distance updates    |
| found     | element pulses `success` twice                         |
| complete  | comparing/swapping/active → sorted/final               |

CSS-driven transitions (Tailwind or Framer Motion for staged motion).
No transition blocks event advancement.

### 6.8 Reduced-Motion Mode

When `prefers-reduced-motion: reduce`:

-   `swap`, `relax` resolve instantly.
-   `compare`, `found` skip pulses.
-   Step advancement still respects the timer; user may disable
    auto-advance and step manually.
-   CodePanel always highlights current line regardless.

### 6.9 Zustand Stores — Split by Concern (SOLID: SRP)

The single `VisualizationStore` is split into two stores with
**distinct change reasons**:

- **`engineStore`** — algorithm execution state. Changes when:
  - User advances steps, plays, pauses.
  - Algorithm module is loaded with new input.
  - Speed changes.

- **`uiStore`** — visualization chrome. Changes when:
  - User toggles code panel.
  - User toggles explanation panel.
  - User changes layout density.

Splitting these prevents UI toggles from re-rendering engine
consumers (and vice versa).

``` ts
// stores/engine-store.ts
interface EngineStore {
  // session
  sessionId: string;
  slug: string | null;

  // algorithm
  module: AlgorithmModule | null;
  events: AlgorithmEvent[];
  currentStep: number;
  status: PlayerStatus;
  speed: number;                   // msPerStep

  // derived view state (typed at consumer site)
  visualizationState: unknown;

  // actions
  load(module: AlgorithmModule, input: unknown): void;
  play(): void;
  pause(): void;
  next(): void;
  prev(): void;
  reset(): void;
  seek(index: number): void;
  setSpeed(ms: number): void;
}

// stores/ui-store.ts
interface UIStore {
  isCodePanelOpen: boolean;
  isExplanationOpen: boolean;
  isCompactLayout: boolean;

  toggleCodePanel(): void;
  toggleExplanationPanel(): void;
  setCompactLayout(compact: boolean): void;
}
```

Neither store holds TanStack Query data.

Selectors compose both stores for the shell component:

``` ts
export const useVisualization = () => {
  const engine = useEngineStore();
  const ui = useUIStore();
  return { ...engine, ...ui };
};

// Granular subscriptions (recommended)
export const useEngineStatus = () => useEngineStore(s => s.status);
export const useCodePanelOpen = () => useUIStore(s => s.isCodePanelOpen);
```

### 6.10 Engine Invariants

1.  `events.length === stepCount` constant across runs with same input.
2.  `currentStep` ∈ `[0, events.length - 1]` when `status !== "idle"`.
3.  Every event's `ElementId` exists in current state or element pool.
4.  `complete` is the last event when present.
5.  Reducer is referentially deterministic.

### 6.11 Public Engine API (Stable Surface)

``` ts
// engine
useEngineStore(): EngineStore
useEngineStatus(): PlayerStatus
useCurrentStep(): number
useEvents(): AlgorithmEvent[]

// UI chrome
useUIStore(): UIStore
useCodePanelOpen(): boolean
useExplanationPanelOpen(): boolean

// composition
useVisualization(): EngineStore & UIStore   // convenience for shell

// adapters
useVisualizationState<S>(adapter: VisualizationAdapter<S>): S

// registry
registerAlgorithm(module: AlgorithmModule): void
getAlgorithm(slug: string): AlgorithmModule | undefined

// errors
EngineInvariantError
registerAlgorithm(module: AlgorithmModule): void
getAlgorithm(slug: string): AlgorithmModule | undefined
EngineInvariantError
```

Anything else in `features/visualization` is internal.

## 7. Component Contracts (Major Surfaces)

These are the minimum props each major component accepts. Components
may accept more; pages may not depend on extras.

``` ts
interface AlgorithmPageProps      { slug: string }

interface VisualizationShellProps {
  slug: string; title: string; description?: string;
  complexity: { best?: string; average?: string;
                worst?: string; space?: string };
  children: React.ReactNode;
}

interface VisualizationCanvasProps {
  adapterKind: VisualizationAdapter<unknown>["kind"];
  state: unknown;
}

interface VisualizationControlsProps {
  status: PlayerStatus;
  canPrev: boolean; canNext: boolean;
  speed: number;
  onPlay: () => void; onPause: () => void;
  onNext: () => void; onPrev: () => void;
  onReset: () => void;
  onSeek: (index: number) => void;
  onSpeedChange: (ms: number) => void;
}

interface CodePanelProps {
  sources: Record<SourceLanguage, string>;
  currentLine?: number;
  language: SourceLanguage;
  onLanguageChange: (lang: SourceLanguage) => void;
}

interface CurrentStepPanelProps {
  currentStep: number; totalSteps: number;
  message?: string; metadata?: Record<string, unknown>;
}

interface AlgorithmCardProps {
  slug: string; name: string; description: string;
  difficulty: "easy" | "medium" | "hard";
  visualizationKind: string;
  bestTime?: string; averageTime?: string;
  worstTime?: string; spaceComplexity?: string;
  topics: string[];
}
```

Rule: if two pages need different props for the same component, split
the component — do not add optional props.

## 8. State Ownership Matrix

Default to the topmost acceptable row.

| Data                                  | Lives in                                    |
|---------------------------------------|---------------------------------------------|
| Authenticated user identity           | AuthProvider context (server-derived)       |
| Server-cached lists                   | TanStack Query                              |
| Server-cached detail                  | TanStack Query                              |
| Current algorithm module + events     | Zustand `visualizationStore`                |
| Current step, status, speed           | Zustand `visualizationStore`                |
| Visualization-derived view state      | Selector over Zustand                       |
| Code panel open/closed                | Zustand `visualizationStore`                |
| Filter selections on explorer pages   | URL search params                           |
| Form state                            | React Hook Form                             |
| Theme                                 | `next-themes` or own context                |
| Transient hover/focus                 | Component-local `useState`                  |

Never put server responses into Zustand or events into TanStack Query.

## 9. Data Fetching & API Client

`lib/api/`:

``` text
client.ts        fetch wrapper: base URL, credentials, error normalization
algorithms.ts    getAlgorithms(filters), getAlgorithm(slug), getCategories()
problems.ts      getProblems(filters), getProblem(slug), getProblemTopics(slug)
progress.ts      getProgress(), updateAlgorithmProgress(), updateProblemProgress()
dashboard.ts     getDashboard()
roadmap.ts       getRoadmap()
users.ts         getMe()
```

Hooks (TanStack Query):

``` text
useAlgorithms(filters)
useAlgorithm(slug)
useProblems(filters)
useProblem(slug)
useDashboard()
useProgress()
useRoadmap()
useMe()
```

API client normalizes errors to `ApiError { code, message, status }`.

## 10. Authentication

-   Server-side concern. HTTP-only cookies when supported.
-   Never store tokens in `localStorage`, `sessionStorage`, or Zustand
    persistence.
-   `AuthProvider`, `useCurrentUser()`, `<ProtectedRoute>`.
-   Public algorithm pages are not gated.

## 11. Forms

-   React Hook Form + Zod.
-   Reusable schemas: `loginSchema`, `registerSchema`,
    `settingsSchema`, `algorithmInputSchema`, `problemFilterSchema`.
-   Validation rules live in one place per form.

## 12. Error / Loading / Empty States

Reusable components: `LoadingState`, `ErrorState`, `EmptyState`. Each
page composes these instead of writing ad-hoc spinners and error
boxes. API errors are normalized by the API client.

## 13. Performance Budget

Targets for `/algorithms/[slug]` on mid-tier hardware:

``` text
First Contentful Paint       < 1.5 s
Time to Interactive          < 2.5 s
Visualization render budget  < 16 ms / step (60 fps)
Bundle (/algorithms/[slug])  < 220 KB gz (excluding engine)
Bundle (engine)              < 90 KB gz
Module (per algorithm)       < 8 KB gz
```

Rules:

-   Algorithm modules dynamically imported per slug.
-   Engine shared across pages.
-   Code highlighter (Shiki/Prism) lazy-loaded on first code panel.
-   No analytics/Sentry/feature-flags in the engine bundle.

## 14. Accessibility

Target: WCAG 2.1 AA.

-   Semantic landmarks on every page.
-   All controls keyboard-reachable; visible focus.
-   Player shortcuts: `Space`, `←`, `→`, `R`.
-   Color never the only status indicator (text/icon required).
-   `prefers-reduced-motion` honored.
-   `prefers-contrast` honored where token-controlled.
-   Form errors announced via `aria-live="polite"`.
-   Audit cadence: axe-core in component tests pre-merge; manual
    keyboard-only walkthrough per release; NVDA + VoiceOver quarterly.

## 15. Responsive Layout

``` text
Desktop   Sidebar + content + optional code/explanation panel
Tablet    Collapsible sidebar + content
Mobile    Top nav, visualization, controls, step explanation,
          code accordion, complexity accordion
```

Visualization must remain usable on mobile (touch-friendly controls,
readable text, no horizontal scroll on standard phones).

## 16. Module Boundaries

| Feature              | Owns                                                       |
|----------------------|------------------------------------------------------------|
| algorithms           | explorer page, algorithm cards, filters                    |
| visualization        | engine, adapters, player, modules, shell, controls, panels |
| data-structures      | catalog and detail pages                                   |
| problems             | list with filters, detail, "Visualize" CTA                 |
| dashboard            | dashboard summary rendering                                |
| auth                 | AuthProvider, login/register pages, ProtectedRoute         |

## 17. SOLID Map

``` text
Single Responsibility   AlgorithmPage composes DataLoader + Player +
                         Renderer + CodePanel + StepPanel
                         engineStore ≠ uiStore (separate change reasons)
                         DashboardService ≠ ReadinessCalculator ≠ StreakCalculator
Open/Closed             new visualization → new adapter + module, no
                         changes to player / shell / controls
                         new dashboard formula → swap a calculator, not
                         the orchestrator
Liskov                  all adapters satisfy VisualizationAdapter<S>
Interface Segregation   ArrayAlgorithmModule | TreeAlgorithmModule |
                         GraphAlgorithmModule (each module implements
                         only what it needs)
                         ArrayVisualizer, GraphVisualizer, TreeVisualizer
Dependency Inversion    UI depends on abstractions (player, adapter,
                         module, ApiClient), not concrete impls
                         Catalog services depend on event dispatcher,
                         not on ProgressService directly
```

## 18. DRY Anchors

Don't duplicate:

-   API calls
-   algorithm metadata
-   filter logic
-   loading/error/empty states
-   button styles
-   player behavior
-   complexity rendering
-   code panel behavior

When duplication appears, first check if it belongs in a hook, utility,
shared component, domain module, registry, or service.

## 19. Testing Strategy

``` text
Unit          algorithm event generation, player, adapters, utils,
              filters, reducer purity
Component     controls, code highlighting, step panel, algorithm
              cards, graph interactions
E2E           minimum flows:
              Home → Algorithms → Quick Sort → Play → Next → Reset
              Home → Problems → Two Sum → Visualize
              Login → Dashboard → Progress
              Algorithms → Search → Binary Search
```

Each algorithm module ships with a **canonical event trace** test to
prevent drift across runs.

## 20. Phase Roadmap

``` text
Phase 1 — Foundation
  • Next.js + TS + Tailwind scaffold, design tokens
  • shadcn/ui setup, layout, navigation
  • Home page with mini sorting demo (uses engine)
  • Algorithms Explorer with mocked data
  • API client + TanStack Query provider

Phase 2 — Engine Core
  • event schema, adapter contract, player state machine
  • ArrayAdapter + Bubble Sort module + canonical trace
  • VisualizationShell, Controls, CodePanel, StepPanel
  • Quick Sort + Linked List data-structure page

Phase 3 — Search & Trees
  • Binary Search (array adapter)
  • TreeAdapter, BST insert/search, traversals
  • HeapAdapter, Heap Sort

Phase 4 — Graphs
  • GraphAdapter (static layout)
  • BFS, DFS, Dijkstra with priority-queue panel

Phase 5 — Auth & Server State
  • AuthProvider, login/register pages
  • Real API integration for catalog
  • Progress reporting (fire-and-forget POST on complete)

Phase 6 — Problems & Dashboard
  • /problems list with filters (server-driven)
  • /problems/[slug] + "Visualize" CTA
  • /dashboard aggregation
  • /roadmap, /settings

Phase 7 — Polish
  • performance audit, bundle splitting
  • a11y audit, shortcut tooltips
  • Playwright E2E for the four critical flows
```

## 21. Definition of Done — Frontend

``` text
□ pages match supplied designs
□ routes work
□ API integration typed end-to-end
□ visualization controls functional
□ algorithm events deterministic
□ code panel highlights current line on every step
□ responsive at desktop/tablet/mobile
□ a11y: keyboard reach, focus visible, color-independent status,
  prefers-reduced-motion honored
□ no unnecessary duplication
□ TypeScript passes
□ ESLint passes
□ Vitest unit + component tests pass
□ Playwright E2E for 4 critical flows passes
□ production build passes
□ engine bundle ≤ 90 KB gz
□ each algorithm module has canonical trace test
□ player state-machine tests pass
□ axe-core shows zero serious/critical violations
□ Lighthouse Performance ≥ 85 on /algorithms/quick-sort (desktop)
□ no algorithm logic in React components (ESLint rule enforced)
```

## 22. Open Questions / Future Decisions

-   Internationalization of event `message` strings (English-first at v1).
-   Sound effects for events (off by default; reduced-motion respects
    this too).
-   Sharing a visualization state via URL (deep link to a specific step).
-   Mobile-native gestures (swipe to step).
-   Offline support via service worker for already-loaded algorithms.
