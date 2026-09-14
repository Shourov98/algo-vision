"""Algorithm seed data (catalog rows + topic M:N).

Kept in a separate module from the insert logic
(``algorithms.py``) so each file stays under the 400-line cap
(see GIT_WORKFLOW §12). The list is curated to cover every
category with at least one algorithm.

Refs: DATABASE_DESIGN.md §7 (Seed Plan)
Refs: ALGOVISION_BACKEND_PLAN.md §3.10 (B3.10 seeds)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final


@dataclass(frozen=True, slots=True)
class AlgorithmSeed:
    """A single algorithm seed row.

    ``category_slug`` and ``topic_slugs`` are FK targets
    resolved at insert time against the deterministic UUIDs
    from ``categories.py`` and ``topics.py``.
    """

    slug: str
    name: str
    category_slug: str
    description: str
    difficulty: str
    visualization_type: str
    best_time: str | None
    average_time: str | None
    worst_time: str | None
    space_complexity: str | None
    topic_slugs: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# The list. Kept canonical + curated; covers every category.
# ---------------------------------------------------------------------------

ALGORITHMS: Final[tuple[AlgorithmSeed, ...]] = (
    # --- Sorting -------------------------------------------------------------
    AlgorithmSeed(
        slug="bubble-sort",
        name="Bubble Sort",
        category_slug="sorting",
        description=(
            "Repeatedly walks the list, comparing adjacent pairs and "
            "swapping them if out of order. Simple but slow; mostly "
            "used as a teaching example."
        ),
        difficulty="easy",
        visualization_type="array",
        best_time="O(n)",
        average_time="O(n^2)",
        worst_time="O(n^2)",
        space_complexity="O(1)",
        topic_slugs=("in-place", "stable"),
    ),
    AlgorithmSeed(
        slug="quick-sort",
        name="Quick Sort",
        category_slug="sorting",
        description=(
            "Picks a pivot and partitions the array around it, "
            "recursing on each side. Fast in practice, though worst-"
            "case is quadratic."
        ),
        difficulty="medium",
        visualization_type="array",
        best_time="O(n log n)",
        average_time="O(n log n)",
        worst_time="O(n^2)",
        space_complexity="O(log n)",
        topic_slugs=("divide-and-conquer", "recursion"),
    ),
    AlgorithmSeed(
        slug="merge-sort",
        name="Merge Sort",
        category_slug="sorting",
        description=(
            "Divides the array in half, sorts each half recursively, "
            "and merges the sorted halves. Stable; guaranteed "
            "O(n log n)."
        ),
        difficulty="medium",
        visualization_type="array",
        best_time="O(n log n)",
        average_time="O(n log n)",
        worst_time="O(n log n)",
        space_complexity="O(n)",
        topic_slugs=("divide-and-conquer", "stable", "recursion"),
    ),
    # --- Searching -----------------------------------------------------------
    AlgorithmSeed(
        slug="binary-search",
        name="Binary Search",
        category_slug="searching",
        description=(
            "Locates a target in a sorted array by repeatedly halving "
            "the search range."
        ),
        difficulty="easy",
        visualization_type="array",
        best_time="O(1)",
        average_time="O(log n)",
        worst_time="O(log n)",
        space_complexity="O(1)",
        topic_slugs=("divide-and-conquer", "binary-search"),
    ),
    # --- Graph ---------------------------------------------------------------
    AlgorithmSeed(
        slug="dijkstra",
        name="Dijkstra's Algorithm",
        category_slug="graph",
        description=(
            "Finds shortest paths from a source vertex in a graph "
            "with non-negative edge weights."
        ),
        difficulty="medium",
        visualization_type="graph",
        best_time="O((V + E) log V)",
        average_time="O((V + E) log V)",
        worst_time="O((V + E) log V)",
        space_complexity="O(V)",
        topic_slugs=("greedy", "heap", "dijkstra"),
    ),
    AlgorithmSeed(
        slug="bfs",
        name="Breadth-First Search",
        category_slug="graph",
        description=(
            "Explores a graph level by level from a source vertex. "
            "Finds shortest paths in unweighted graphs."
        ),
        difficulty="easy",
        visualization_type="graph",
        best_time="O(V + E)",
        average_time="O(V + E)",
        worst_time="O(V + E)",
        space_complexity="O(V)",
        topic_slugs=("bfs", "recursion"),
    ),
    AlgorithmSeed(
        slug="dfs",
        name="Depth-First Search",
        category_slug="graph",
        description=(
            "Explores a graph by going as deep as possible along each "
            "branch before backtracking."
        ),
        difficulty="easy",
        visualization_type="graph",
        best_time="O(V + E)",
        average_time="O(V + E)",
        worst_time="O(V + E)",
        space_complexity="O(V)",
        topic_slugs=("dfs", "recursion"),
    ),
    # --- Dynamic Programming -------------------------------------------------
    AlgorithmSeed(
        slug="fibonacci",
        name="Fibonacci (Memoized)",
        category_slug="dynamic-programming",
        description=(
            "Computes the nth Fibonacci number with memoization — a "
            "canonical dynamic-programming example."
        ),
        difficulty="easy",
        visualization_type="array",
        best_time="O(n)",
        average_time="O(n)",
        worst_time="O(n)",
        space_complexity="O(n)",
        topic_slugs=("memoization", "recursion"),
    ),
    AlgorithmSeed(
        slug="knapsack-01",
        name="0/1 Knapsack",
        category_slug="dynamic-programming",
        description=(
            "Selects a subset of items with maximum total value while "
            "respecting a weight capacity."
        ),
        difficulty="hard",
        visualization_type="array",
        best_time="O(n W)",
        average_time="O(n W)",
        worst_time="O(n W)",
        space_complexity="O(n W)",
        topic_slugs=("memoization",),
    ),
    # --- Greedy --------------------------------------------------------------
    AlgorithmSeed(
        slug="activity-selection",
        name="Activity Selection",
        category_slug="greedy",
        description=(
            "Selects the maximum number of non-overlapping activities "
            "using a greedy interval-scheduling strategy."
        ),
        difficulty="medium",
        visualization_type="array",
        best_time="O(n log n)",
        average_time="O(n log n)",
        worst_time="O(n log n)",
        space_complexity="O(1)",
        topic_slugs=("greedy",),
    ),
    # --- Divide & Conquer -----------------------------------------------------
    AlgorithmSeed(
        slug="karatsuba",
        name="Karatsuba Multiplication",
        category_slug="divide-and-conquer",
        description=(
            "Multiplies two n-digit integers in O(n^log2(3)) ~ O(n^1.585) "
            "by recursively splitting the operands — a classic "
            "divide-and-conquer speedup over the O(n^2) grade-school "
            "algorithm."
        ),
        difficulty="hard",
        visualization_type="array",
        best_time="O(n^1.585)",
        average_time="O(n^1.585)",
        worst_time="O(n^1.585)",
        space_complexity="O(n)",
        topic_slugs=("divide-and-conquer", "recursion"),
    ),
    # --- String --------------------------------------------------------------
    AlgorithmSeed(
        slug="kmp",
        name="Knuth-Morris-Pratt",
        category_slug="string",
        description=(
            "Searches for a pattern in a text in linear time using a "
            "failure-function pre-computation."
        ),
        difficulty="hard",
        visualization_type="array",
        best_time="O(n + m)",
        average_time="O(n + m)",
        worst_time="O(n + m)",
        space_complexity="O(m)",
        topic_slugs=("kmp",),
    ),
    # --- Tree ----------------------------------------------------------------
    AlgorithmSeed(
        slug="inorder-traversal",
        name="Inorder Traversal",
        category_slug="tree",
        description=(
            "Visits a binary tree's left subtree, root, then right "
            "subtree — yields sorted order for BSTs."
        ),
        difficulty="easy",
        visualization_type="tree",
        best_time="O(n)",
        average_time="O(n)",
        worst_time="O(n)",
        space_complexity="O(h)",
        topic_slugs=("dfs", "recursion"),
    ),
)


__all__ = ["ALGORITHMS", "AlgorithmSeed"]
