"""Seed data for ``problems`` + their ``problem_topics`` /
``problem_companies`` join rows.

The list of problems lives apart from the insert logic
(``problems.py``) so each file stays readable. The data
is the product surface - reviewers see it in PRs - and
the insert logic is plumbing. Splitting them keeps each
file well under the 400-line cap (GIT_WORKFLOW §12).

Count rationale
---------------
DATABASE_DESIGN §3 caps problems at <5k rows. The seed
ships a starter set of 12 well-known interview problems so
the problems API has content to render; the rest land as
content decisions are made (not as a tech task). The list
deliberately spans difficulty (easy -> hard) and
visualization availability so both the editor flow and the
visualization flow have something to render.

Slug conventions
----------------
- ``two-sum``           -> arrays + hash-map, easy
- ``reverse-linked-list`` -> linked-list visualization
- ``lru-cache``         -> design + hash-map + linked-list
- ``merge-k-sorted-lists`` -> heap visualization
- ``word-break``        -> DP, no visualization
- ``n-queens``          -> backtracking, no visualization
- ``course-schedule``   -> graph + BFS, has visualization
- ``longest-substring-without-repeating-characters`` -> sliding window
- ``minimum-window-substring`` -> sliding window
- ``valid-parentheses`` -> stack visualization
- ``trapping-rain-water`` -> two-pointer visualization
- ``median-of-two-sorted-arrays`` -> binary search

Why ``external_reference`` uses free-form tags (``LC-1``)
---------------------------------------------------------
DATABASE_DESIGN §1: ``external_reference`` is a free-text
column. We use ``LC-`` prefixes for LeetCode IDs, ``HR-``
for HackerRank IDs, etc. Some problems have no external
reference (none yet) and the column is nullable.

Refs: DATABASE_DESIGN.md §7 (Seed Plan), §3 (volume)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 4 - B4.10)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final


@dataclass(frozen=True, slots=True)
class ProblemSeed:
    """A single problem seed row.

    ``topic_slugs`` and ``company_slugs`` reference the
    catalog ``topics`` and problems ``companies`` seed
    rows. Rows referencing unknown slugs are skipped at
    insert time so the seed is robust to a partially-
    seeded database.

    ``solution_explanation`` is intentionally short for v1;
    the editorial gets fleshed out as content lands. None
    means "no editorial yet" (the column is nullable).
    """

    slug: str
    title: str
    description: str
    difficulty: str  # "easy" | "medium" | "hard"
    solution_explanation: str | None
    external_reference: str | None
    visualization_available: bool
    topic_slugs: tuple[str, ...] = field(default_factory=tuple)
    company_slugs: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# The list. Order = display order (newest at top); keep stable
# across edits so re-runs don't shuffle the listing.
# ---------------------------------------------------------------------------

PROBLEMS: Final[tuple[ProblemSeed, ...]] = (
    ProblemSeed(
        slug="two-sum",
        title="Two Sum",
        description=(
            "Given an array of integers ``nums`` and an integer "
            "``target``, return indices of the two numbers such "
            "that they add up to ``target``. You may assume that "
            "each input would have exactly one solution, and you "
            "may not use the same element twice."
        ),
        difficulty="easy",
        solution_explanation=(
            "Use a hash map from value to index. Iterate once; for "
            "each ``nums[i]``, check if ``target - nums[i]`` is in "
            "the map. If yes, return the pair; if no, store "
            "``nums[i] -> i``. O(n) time, O(n) space."
        ),
        external_reference="LC-1",
        visualization_available=True,
        topic_slugs=("hashing",),
        company_slugs=("google", "amazon", "meta", "uber"),
    ),
    ProblemSeed(
        slug="reverse-linked-list",
        title="Reverse Linked List",
        description=(
            "Given the ``head`` of a singly linked list, reverse "
            "the list, and return the reversed list."
        ),
        difficulty="easy",
        solution_explanation=(
            "Iteratively flip three pointers per node: "
            "``prev <- curr <- next``. O(n) time, O(1) space."
        ),
        external_reference="LC-206",
        visualization_available=True,
        topic_slugs=("recursion",),
        company_slugs=("amazon", "microsoft", "apple"),
    ),
    ProblemSeed(
        slug="valid-parentheses",
        title="Valid Parentheses",
        description=(
            "Given a string ``s`` containing just the characters "
            "``()[]{}``, determine if the input string is valid. "
            "An input is valid if open brackets are closed by the "
            "same type and in the correct order."
        ),
        difficulty="easy",
        solution_explanation=(
            "Push every opening bracket onto a stack; for every "
            "closing bracket, pop and compare. The string is valid "
            "iff the stack is empty at the end. O(n) time, O(n) "
            "space."
        ),
        external_reference="LC-20",
        visualization_available=True,
        topic_slugs=("hashing",),
        company_slugs=("google", "meta", "amazon", "linkedin"),
    ),
    ProblemSeed(
        slug="merge-k-sorted-lists",
        title="Merge k Sorted Lists",
        description=(
            "You are given an array of ``k`` linked lists, each "
            "sorted in ascending order. Merge all the linked "
            "lists into one sorted linked list and return it."
        ),
        difficulty="hard",
        solution_explanation=(
            "Use a min-heap of size ``k``. Pop the smallest head, "
            "push that node's next. O(n log k) time, O(k) space."
        ),
        external_reference="LC-23",
        visualization_available=True,
        topic_slugs=("heap", "divide-and-conquer"),
        company_slugs=("google", "amazon", "meta", "uber"),
    ),
    ProblemSeed(
        slug="lru-cache",
        title="LRU Cache",
        description=(
            "Design a data structure that follows the constraints "
            "of a Least Recently Used (LRU) cache. Implement the "
            "``LRUCache`` class with ``get(key)`` and "
            "``put(key, value)`` running in O(1)."
        ),
        difficulty="medium",
        solution_explanation=(
            "Combine a hash map (key -> node) with a doubly-"
            "linked list (recency order). On get / put, move "
            "the touched node to the head; on eviction, drop "
            "the tail. O(1) for both ops."
        ),
        external_reference="LC-146",
        visualization_available=False,
        topic_slugs=("hashing", "in-place"),
        company_slugs=("google", "amazon", "meta", "microsoft"),
    ),
    ProblemSeed(
        slug="longest-substring-without-repeating-characters",
        title=(
            "Longest Substring Without Repeating Characters"
        ),
        description=(
            "Given a string ``s``, find the length of the longest "
            "substring without repeating characters."
        ),
        difficulty="medium",
        solution_explanation=(
            "Sliding window with a hash map of last-seen index. "
            "For each right index, advance ``left`` to one past "
            "the previous occurrence of ``s[right]``. O(n) time, "
            "O(min(n, sigma)) space."
        ),
        external_reference="LC-3",
        visualization_available=True,
        topic_slugs=("sliding-window", "hashing"),
        company_slugs=("amazon", "meta", "uber"),
    ),
    ProblemSeed(
        slug="minimum-window-substring",
        title="Minimum Window Substring",
        description=(
            "Given two strings ``s`` and ``t``, return the minimum "
            "window substring of ``s`` such that every character "
            "in ``t`` (including duplicates) is included in the "
            "window. If no such substring exists, return ``\"\"``."
        ),
        difficulty="hard",
        solution_explanation=(
            "Sliding window with a deficit counter. Expand right "
            "until the window covers ``t``; then contract left "
            "while the window still covers ``t``. O(n + m) time, "
            "O(sigma) space."
        ),
        external_reference="LC-76",
        visualization_available=False,
        topic_slugs=("sliding-window", "hashing"),
        company_slugs=("meta", "linkedin", "uber"),
    ),
    ProblemSeed(
        slug="course-schedule",
        title="Course Schedule",
        description=(
            "There are a total of ``numCourses`` courses you have "
            "to take, labeled from ``0`` to ``numCourses - 1``. "
            "You are given an array ``prerequisites`` where "
            "``prerequisites[i] = [a, b]`` means you must take "
            "course ``b`` first if you want to take course ``a``. "
            "Return ``true`` if you can finish all courses."
        ),
        difficulty="medium",
        solution_explanation=(
            "Detect a cycle in the directed graph of "
            "prerequisites. Topological sort via Kahn's algorithm "
            "(BFS) - if every node is processed, the graph is a "
            "DAG and all courses are finishable. O(V + E) time."
        ),
        external_reference="LC-207",
        visualization_available=True,
        topic_slugs=("bfs", "topological-sort"),
        company_slugs=("google", "amazon", "meta", "uber"),
    ),
    ProblemSeed(
        slug="n-queens",
        title="N-Queens",
        description=(
            "The n-queens puzzle is the problem of placing ``n`` "
            "queens on an ``n x n`` chessboard such that no two "
            "queens attack each other. Return all distinct "
            "solutions to the n-queens puzzle."
        ),
        difficulty="hard",
        solution_explanation=(
            "Backtrack row by row. For each row, try every column "
            "and check the three attack axes (column, "
            "positive-slope diagonal, negative-slope diagonal) "
            "via O(1) set lookups. O(n!) worst-case time."
        ),
        external_reference="LC-51",
        visualization_available=False,
        topic_slugs=("backtracking",),
        company_slugs=("amazon", "microsoft"),
    ),
    ProblemSeed(
        slug="word-break",
        title="Word Break",
        description=(
            "Given a string ``s`` and a dictionary of strings "
            "``wordDict``, return ``true`` if ``s`` can be "
            "segmented into a space-separated sequence of one or "
            "more dictionary words."
        ),
        difficulty="medium",
        solution_explanation=(
            "Bottom-up DP. ``dp[i] = true`` iff some ``j < i`` "
            "satisfies ``dp[j] and s[j:i] in wordDict``. O(n * L) "
            "time where L is the average word length; can be "
            "improved with a Trie."
        ),
        external_reference="LC-139",
        visualization_available=False,
        topic_slugs=("memoization",),
        company_slugs=("amazon", "meta", "uber", "linkedin"),
    ),
    ProblemSeed(
        slug="trapping-rain-water",
        title="Trapping Rain Water",
        description=(
            "Given ``n`` non-negative integers representing an "
            "elevation map where the width of each bar is ``1``, "
            "compute how much water it can trap after raining."
        ),
        difficulty="hard",
        solution_explanation=(
            "Two-pointer scan. Track the tallest bar seen from "
            "each side; advance the side with the smaller max, "
            "trapping ``max_side - height[i]`` water at index "
            "``i``. O(n) time, O(1) space."
        ),
        external_reference="LC-42",
        visualization_available=True,
        topic_slugs=("two-pointers", "hashing"),
        company_slugs=("google", "amazon", "meta", "uber"),
    ),
    ProblemSeed(
        slug="median-of-two-sorted-arrays",
        title="Median of Two Sorted Arrays",
        description=(
            "Given two sorted arrays ``nums1`` and ``nums2`` of "
            "size ``m`` and ``n`` respectively, return the median "
            "of the two sorted arrays. The overall run time "
            "complexity should be O(log (m+n))."
        ),
        difficulty="hard",
        solution_explanation=(
            "Binary search the partition point on the smaller "
            "array. The correct partition splits the combined "
            "array so every left-half element is <= every right-"
            "half element. O(log(min(m, n))) time."
        ),
        external_reference="LC-4",
        visualization_available=False,
        topic_slugs=("binary-search", "divide-and-conquer"),
        company_slugs=("google", "amazon", "apple", "microsoft"),
    ),
)


__all__ = ["PROBLEMS", "ProblemSeed"]
