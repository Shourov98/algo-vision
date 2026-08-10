# AlgoVision Frontend Architecture & CLI LLM Implementation Guide

## 1. Purpose

This document is the implementation contract for the **AlgoVision
frontend**.

The frontend must be built with:

-   **Next.js**
-   **TypeScript**
-   **App Router**
-   **Tailwind CSS**
-   **shadcn/ui** where useful
-   **Zustand** for client-side visualization state
-   **Framer Motion** only where animation adds meaning
-   **TanStack Query** for server state/API caching
-   **React Hook Form + Zod** for forms
-   **Vitest + React Testing Library** for unit/component tests
-   **Playwright** for critical end-to-end flows

The frontend must reproduce the supplied AlgoVision designs as closely
as practical.

The supplied design references define the visual language and page
composition:

-   `AlgoVision — Home.svg`
-   `Explore Algorithms — AlgoVision.svg`
-   `Quick Sort Visualization — AlgoVision.svg`
-   `Dijkstra's Algorithm — AlgoVision.svg`
-   `Linked List Visualization — AlgoVision.svg`
-   `Interview Preparation — AlgoVision.svg`
-   `Dashboard — AlgoVision.svg`

Do not replace the visual direction with a generic dashboard template.

------------------------------------------------------------------------

# 2. Product Principle

AlgoVision is not a normal CRUD website.

The central product experience is:

> **Algorithm execution → deterministic step events → visualization
> state → code highlighting → explanation**

The frontend must therefore be designed around an
**execution/visualization engine**, not around individual page
components.

The architecture must allow a new algorithm to be added without
rewriting:

-   the player controls
-   the visualization state machine
-   the code panel
-   the step explanation panel
-   the progress bar
-   the page layout

------------------------------------------------------------------------

# 3. Design Language

The supplied designs establish the following visual direction.

## Theme

Dark-first developer-tool UI.

Approximate design tokens:

``` text
Background       #0B0F14
Surface          #11161D
Card             #151B23
Border           #252C36
Primary text     #F3F4F6
Secondary text   #9AA3B2
Muted text       #667085
Accent           #8B6CFF
Success          #22C55E
Warning          #F59E0B
Danger           #EF4444
```

Do not hard-code these values throughout components. Define them
centrally as design tokens/CSS variables.

## Typography

Use:

-   Inter or equivalent sans-serif for UI
-   JetBrains Mono or equivalent monospace font for code/data

## Visual behavior

Prefer:

-   subtle borders
-   restrained shadows
-   compact spacing
-   clear hierarchy
-   small-radius controls
-   meaningful animation
-   dense developer-tool layouts

Avoid:

-   excessive glassmorphism
-   large decorative gradients
-   oversized cards
-   childish illustrations
-   excessive rounded containers
-   animations unrelated to algorithm state

------------------------------------------------------------------------

# 4. Pages Required

Use Next.js App Router.

Recommended routes:

``` text
/
 /algorithms
 /algorithms/[slug]

 /data-structures
 /data-structures/[slug]

 /problems
 /problems/[slug]
 /problems/[slug]/visualize

 /dashboard
 /roadmap

 /settings
 /documentation
```

The exact URL naming can be adjusted only if it improves consistency.

------------------------------------------------------------------------

# 5. Page Responsibilities

## Home

Reference: `AlgoVision — Home.svg`

The home page should communicate the product immediately.

Required:

-   AlgoVision navigation
-   hero heading: `See algorithms think.`
-   short product description
-   `Explore Algorithms` CTA
-   interactive mini sorting visualization
-   footer

The hero visualization should use the same visualization primitives as
the actual algorithm pages.

Do not create a separate fake visualization implementation.

------------------------------------------------------------------------

## Algorithm Explorer

Reference: `Explore Algorithms — AlgoVision.svg`

Layout:

``` text
┌──────────────┬─────────────────────────────────────────┐
│ Explorer     │ Page heading                            │
│              │ Description                             │
│ Categories   │ Filters                                 │
│              │ Algorithm cards                         │
│ Sorting      │                                         │
│ Searching    │                                         │
│ Graphs       │                                         │
│ Trees        │                                         │
└──────────────┴─────────────────────────────────────────┘
```

Features:

-   category navigation
-   search
-   difficulty filter
-   algorithm cards
-   complexity metadata
-   algorithm preview
-   open visualization

Cards should be data-driven.

Do not manually duplicate cards in JSX.

------------------------------------------------------------------------

# 6. Algorithm Visualization Architecture

Reference:

-   `Quick Sort Visualization — AlgoVision.svg`
-   `Dijkstra's Algorithm — AlgoVision.svg`

This is the most important frontend module.

Create:

``` text
features/visualization/
    engine/
    player/
    state/
    events/
    components/
    adapters/
```

Recommended components:

``` text
VisualizationShell
VisualizationHeader
VisualizationCanvas
VisualizationControls
CurrentStepPanel
CodePanel
ExplanationPanel
ComplexityPanel
```

------------------------------------------------------------------------

# 7. Execution Event Model

Create a generic event model.

Example:

``` ts
export type AlgorithmEvent =
  | {
      type: "compare";
      ids: string[];
      line?: number;
      message: string;
    }
  | {
      type: "swap";
      ids: [string, string];
      line?: number;
      message: string;
    }
  | {
      type: "visit";
      id: string;
      line?: number;
      message: string;
    }
  | {
      type: "select";
      ids: string[];
      line?: number;
      message: string;
    }
  | {
      type: "insert";
      id: string;
      value: unknown;
      line?: number;
      message: string;
    }
  | {
      type: "delete";
      id: string;
      line?: number;
      message: string;
    }
  | {
      type: "relax";
      from: string;
      to: string;
      line?: number;
      message: string;
    }
  | {
      type: "found";
      ids: string[];
      line?: number;
      message: string;
    }
  | {
      type: "complete";
      message: string;
    };
```

Do not put React state into algorithm implementations.

Algorithms should produce deterministic events.

------------------------------------------------------------------------

# 8. Visualization Adapter Pattern

Every data type gets a visualization adapter.

Example:

``` ts
interface VisualizationAdapter<TState> {
  createInitialState(input: unknown): TState;
  applyEvent(state: TState, event: AlgorithmEvent): TState;
}
```

Examples:

``` text
ArrayVisualizationAdapter
LinkedListVisualizationAdapter
TreeVisualizationAdapter
GraphVisualizationAdapter
HeapVisualizationAdapter
DpTableVisualizationAdapter
RecursionTreeVisualizationAdapter
```

This prevents algorithm-specific rendering logic from leaking into
common components.

------------------------------------------------------------------------

# 9. Execution Player

Create a reusable player.

Required controls:

-   play
-   pause
-   next
-   previous
-   reset
-   speed
-   current step
-   total steps

API:

``` ts
interface ExecutionPlayer {
  play(): void;
  pause(): void;
  next(): void;
  previous(): void;
  reset(): void;
}
```

State:

``` ts
interface ExecutionState {
  steps: AlgorithmEvent[];
  currentStep: number;
  isPlaying: boolean;
  speed: number;
}
```

The player must not know whether it is visualizing:

-   an array
-   a linked list
-   a tree
-   a graph
-   a DP table

It only advances events.

------------------------------------------------------------------------

# 10. Algorithm Registry

Create a frontend registry.

``` ts
interface AlgorithmModule {
  slug: string;
  createExecution(input: unknown): AlgorithmEvent[];
  visualization: VisualizationType;
}
```

Example:

``` text
algorithmRegistry
    ├── bubble-sort
    ├── quick-sort
    ├── merge-sort
    ├── binary-search
    ├── bfs
    ├── dfs
    └── dijkstra
```

The registry should be the only place that maps a backend algorithm slug
to a frontend execution implementation.

Avoid repeated `if/else` or `switch` statements scattered across pages.

------------------------------------------------------------------------

# 11. Sorting Visualization

For:

-   Bubble Sort
-   Selection Sort
-   Insertion Sort
-   Merge Sort
-   Quick Sort
-   Heap Sort

Use a reusable array visualization.

Each element should have:

``` ts
interface ArrayItem {
  id: string;
  value: number;
  status: "idle" | "active" | "comparing" | "swapping" | "sorted" | "pivot";
}
```

Important:

Use stable IDs rather than using array indexes as identity when elements
move.

This avoids React reconciliation bugs during swaps.

------------------------------------------------------------------------

# 12. Graph Visualization

The Dijkstra design shows a graph in the central canvas.

Create:

``` text
GraphCanvas
GraphNode
GraphEdge
GraphControls
PriorityQueuePanel
DistancePanel
```

Graph state should be independent from SVG/canvas rendering.

Recommended domain model:

``` ts
interface GraphNode {
  id: string;
  label: string;
  x: number;
  y: number;
}

interface GraphEdge {
  id: string;
  from: string;
  to: string;
  weight?: number;
  directed?: boolean;
}
```

The renderer should consume this state.

Do not store DOM references inside graph domain objects.

------------------------------------------------------------------------

# 13. Linked List Visualization

Reference: `Linked List Visualization — AlgoVision.svg`

Support:

-   search
-   add front
-   add back
-   delete
-   reverse
-   step-by-step traversal

Separate:

``` text
LinkedList domain state
        ↓
LinkedList visualization adapter
        ↓
LinkedList canvas
```

Do not embed linked-list mutation logic directly in the visual
component.

------------------------------------------------------------------------

# 14. Code Panel

The designs contain an implementation panel with syntax-highlighted code
and highlighted current lines.

Create:

``` text
CodePanel
CodeLine
CodeHeader
LanguageSelector
```

Algorithm metadata should provide:

``` ts
interface SourceCode {
  language: "typescript" | "javascript" | "python" | "java" | "cpp";
  source: string;
}
```

Every execution event may contain:

``` ts
line?: number;
```

The CodePanel highlights that line.

Do not execute arbitrary code in the browser.

The code displayed is educational source code, while the visualization
engine uses controlled algorithm implementations.

------------------------------------------------------------------------

# 15. Current Step Panel

Every visualization page needs a current-step explanation.

Example:

``` text
CURRENT STEP

Partitioning the array around pivot 42.
Comparing 80 with pivot.
```

Display:

-   current step
-   total steps
-   event message
-   optional operation metadata

Example:

``` text
Step 12 / 36
```

------------------------------------------------------------------------

# 16. Animation Rules

Animation is functional.

Examples:

### Compare

Elements briefly become highlighted.

### Swap

Elements move to their new positions.

### Visit

Graph node transitions to visited state.

### Relax

Graph edge and destination distance update.

### Found

Target receives a success state.

### Complete

Visualization settles into final state.

Do not use animation merely for decoration.

Respect:

``` css
prefers-reduced-motion
```

When reduced motion is enabled, state changes must remain understandable
without movement.

------------------------------------------------------------------------

# 17. Data Fetching

Use TanStack Query for server state.

Examples:

``` text
useAlgorithms()
useAlgorithm(slug)
useProblems()
useProblem(slug)
useDashboard()
useProgress()
```

Keep API fetching separate from visualization state.

Do not put server response data directly into Zustand unless there is a
clear reason.

------------------------------------------------------------------------

# 18. API Client

Create a typed API client:

``` text
lib/api/
    client.ts
    algorithms.ts
    problems.ts
    progress.ts
    users.ts
```

The client should:

-   centralize base URL
-   centralize authentication behavior
-   normalize errors
-   expose typed methods

Example:

``` ts
getAlgorithms()
getAlgorithm(slug)
getProblems(filters)
getDashboard()
updateProgress(payload)
```

Never call `fetch()` directly from arbitrary UI components.

------------------------------------------------------------------------

# 19. Authentication

The frontend should treat authentication as a server concern.

Use secure HTTP-only cookies when supported by the backend.

Do not store access tokens in:

-   localStorage
-   sessionStorage
-   Zustand persistence

unless the authentication architecture explicitly requires it.

Create:

``` text
AuthProvider
useCurrentUser()
ProtectedRoute
```

Dashboard and user-specific progress should require authentication.

Public algorithm exploration should not.

------------------------------------------------------------------------

# 20. Forms

Use:

-   React Hook Form
-   Zod

Validate:

-   login
-   registration
-   settings
-   algorithm input
-   problem filters

Validation schemas should be reusable.

Do not duplicate validation rules in multiple components.

------------------------------------------------------------------------

# 21. Error Handling

Create consistent states:

``` text
Loading
Empty
Error
Success
```

Use reusable:

``` text
LoadingState
ErrorState
EmptyState
```

API errors should be normalized by the API client.

Do not display raw backend stack traces to users.

------------------------------------------------------------------------

# 22. Dashboard

Reference: `Dashboard — AlgoVision.svg`

The dashboard contains:

-   algorithms learned
-   problems solved
-   interview readiness
-   current streak
-   activity
-   skill mapping
-   focus areas
-   recently viewed

Do not calculate user metrics independently in several components.

Use a single dashboard API response:

``` ts
interface DashboardSummary {
  algorithmsLearned: number;
  algorithmsTotal: number;
  problemsSolved: number;
  interviewReadiness: number;
  currentStreak: number;
  activity: ActivityPoint[];
  skillMapping: SkillMetric[];
  focusAreas: FocusArea[];
  recentlyViewed: RecentlyViewed[];
}
```

------------------------------------------------------------------------

# 23. Interview Problems

Reference: `Interview Preparation — AlgoVision.svg`

Support:

-   difficulty filters
-   topic filters
-   company filters
-   status
-   sorting
-   visualize/resume actions

Do not hardcode filter logic in the table.

Create reusable query/filter objects.

------------------------------------------------------------------------

# 24. Responsive Design

Desktop:

``` text
Sidebar + content + optional code/explanation panel
```

Tablet:

``` text
Collapsible sidebar + content
```

Mobile:

``` text
Top navigation
Visualization
Controls
Step explanation
Code accordion
Complexity accordion
```

The visualization must remain usable on mobile.

------------------------------------------------------------------------

# 25. Accessibility

Every interactive element must be keyboard accessible.

Requirements:

-   semantic HTML
-   focus states
-   aria labels
-   keyboard controls
-   color-independent status indicators
-   reduced-motion support

For visualization controls, support keyboard shortcuts where
appropriate:

``` text
Space      Play/Pause
ArrowRight Next step
ArrowLeft  Previous step
R          Reset
```

Show shortcuts in tooltips/documentation.

------------------------------------------------------------------------

# 26. SOLID Principles

## Single Responsibility

A component should have one reason to change.

Bad:

``` text
AlgorithmPage
    fetches API
    runs algorithm
    manages playback
    renders graph
    renders code
```

Good:

``` text
AlgorithmPage
AlgorithmDataLoader
ExecutionPlayer
VisualizationRenderer
CodePanel
StepPanel
```

## Open/Closed

Adding a new visualization should not require changing the core player.

Use adapters and registries.

## Liskov Substitution

Visualization adapters must satisfy the same adapter contract.

## Interface Segregation

Do not create one giant interface for every visualization.

Prefer:

``` ts
ArrayVisualizer
GraphVisualizer
TreeVisualizer
```

specific contracts where needed.

## Dependency Inversion

UI components depend on abstractions:

``` text
ExecutionPlayer
VisualizationAdapter
AlgorithmModule
ApiClient
```

not concrete implementations.

------------------------------------------------------------------------

# 27. DRY Rules

Do not duplicate:

-   API calls
-   algorithm metadata
-   filter logic
-   loading states
-   error states
-   button styles
-   visualization controls
-   complexity rendering
-   code panel behavior
-   player behavior

If the same behavior appears twice, first determine whether it belongs
in:

-   a hook
-   a utility
-   a shared component
-   a domain module
-   a registry
-   a service

Do not prematurely create abstractions for unrelated UI.

------------------------------------------------------------------------

# 28. Suggested Directory Structure

``` text
src/
├── app/
│   ├── (public)/
│   │   ├── page.tsx
│   │   ├── algorithms/
│   │   ├── data-structures/
│   │   └── problems/
│   ├── (authenticated)/
│   │   ├── dashboard/
│   │   ├── roadmap/
│   │   └── settings/
│   ├── api/
│   ├── layout.tsx
│   └── globals.css
│
├── components/
│   ├── ui/
│   ├── layout/
│   ├── navigation/
│   └── feedback/
│
├── features/
│   ├── algorithms/
│   ├── visualization/
│   ├── data-structures/
│   ├── problems/
│   ├── dashboard/
│   └── auth/
│
├── lib/
│   ├── api/
│   ├── auth/
│   ├── query/
│   └── utils/
│
├── stores/
│   └── visualization-store.ts
│
├── hooks/
│
├── types/
│
└── tests/
```

Feature-specific code should stay inside the feature.

------------------------------------------------------------------------

# 29. Testing

Required tests:

## Unit

Test:

-   algorithm event generation
-   execution player
-   adapters
-   utility functions
-   filters

## Component

Test:

-   controls
-   code highlighting
-   step panel
-   algorithm cards
-   graph interactions

## E2E

At minimum:

``` text
Home → Algorithms → Quick Sort → Play → Next → Reset

Home → Problems → Two Sum → Visualize

Login → Dashboard → Progress

Algorithms → Search → Binary Search
```

------------------------------------------------------------------------

# 30. CLI LLM Instructions

The following section is intended to be pasted into a CLI coding agent
such as a configured **z.ai CLI, Claude Code, Gemini CLI, Codex CLI, or
similar terminal LLM agent**.

## Master Agent Instruction

``` text
You are the senior frontend engineer responsible for implementing AlgoVision.

Read FRONTEND.md completely before changing code.

The supplied SVG design references are the source of truth for visual composition and terminology.

Your responsibilities:

1. Build the application using Next.js App Router and TypeScript.
2. Follow SOLID and DRY.
3. Keep domain logic separate from UI.
4. Build a reusable algorithm execution engine.
5. Build reusable visualization adapters.
6. Never duplicate algorithm/player/UI logic.
7. Never create fake buttons or fake interactions.
8. Do not replace the supplied visual language with a generic dashboard.
9. Do not introduce a dependency unless it solves a real problem.
10. Write tests for important domain behavior.
11. Run lint, typecheck, tests, and build after meaningful changes.
12. Never silently modify architecture to avoid a difficult implementation.
13. If an architectural decision is uncertain, inspect the repository first and explain the tradeoff.
14. Never delete existing working functionality without explicit justification.
15. Do not implement backend functionality inside the frontend.
16. Do not execute arbitrary user-provided code.

Implementation priority:

Phase 1:
- project foundation
- design system
- layout
- home
- algorithms explorer

Phase 2:
- execution engine
- player controls
- Bubble Sort
- Quick Sort
- Binary Search

Phase 3:
- Linked List
- Stack
- Queue
- Tree

Phase 4:
- Graph
- BFS
- DFS
- Dijkstra

Phase 5:
- problems
- dashboard
- progress
- polish

For every feature:
- inspect existing architecture
- identify reusable abstractions
- implement domain logic
- implement tests
- implement UI
- verify behavior
- run typecheck/lint/tests
```

------------------------------------------------------------------------

# 31. CLI Workflow

The agent should follow this workflow for every task:

``` text
1. Read requirements.
2. Inspect repository.
3. Identify affected modules.
4. Create implementation plan.
5. Implement smallest coherent unit.
6. Run tests/typecheck.
7. Review SOLID/DRY.
8. Continue to next unit.
9. Run full verification.
```

Do not ask the LLM to implement the entire application blindly in one
generation.

Use small vertical slices.

------------------------------------------------------------------------

# 32. Recommended CLI Task Prompt

``` text
Implement the next vertical slice of AlgoVision.

First inspect:
- FRONTEND.md
- existing source tree
- package.json
- current routing
- existing components
- existing tests

Then:

1. Explain the current architecture briefly.
2. Identify reusable components.
3. Implement the requested feature.
4. Keep algorithm logic independent from React.
5. Add tests.
6. Run:
   - typecheck
   - lint
   - unit tests
   - production build if practical
7. Report:
   - files changed
   - architecture decisions
   - tests executed
   - remaining issues

Do not rewrite unrelated code.
```

------------------------------------------------------------------------

# 33. Definition of Done

Frontend work is complete only when:

-   pages match the supplied designs
-   routes work
-   API integration is typed
-   visualization controls are functional
-   algorithm events are deterministic
-   code highlighting follows execution
-   responsive behavior works
-   accessibility is addressed
-   no unnecessary duplication exists
-   TypeScript passes
-   lint passes
-   tests pass
-   production build passes
