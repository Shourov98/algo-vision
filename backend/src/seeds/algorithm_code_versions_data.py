"""Code-version seed data (one Python snippet per algorithm).

Kept in a separate module from the insert logic
(``algorithm_code_versions.py``) so each file stays under the
400-line cap (GIT_WORKFLOW §12).

Why Python only in the seed
---------------------------
The schema supports multiple languages; the frontend is
the consumer that picks the active language per render.
Seeding just Python keeps the seed reviewable and matches
the visual references (which are SVG, not code). Java and
C++ samples arrive when the multi-language UI lands.

Refs: DATABASE_DESIGN.md §7 (Seed Plan)
Refs: ALGOVISION_BACKEND_PLAN.md §3.10 (B3.10 seeds)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class CodeVersionSeed:
    """A single (algorithm_slug, language, version) row.

    Source code is short and educational — we are not
    shipping production reference implementations, just
    enough to render the algorithm page.
    """

    algorithm_slug: str
    language: str
    source_code: str


# ---------------------------------------------------------------------------
# The list. Source: hand-written canonical samples.
# ---------------------------------------------------------------------------

CODE_VERSIONS: Final[tuple[CodeVersionSeed, ...]] = (
    CodeVersionSeed(
        algorithm_slug="bubble-sort",
        language="python",
        source_code=(
            "def bubble_sort(arr: list[int]) -> list[int]:\n"
            "    a = list(arr)\n"
            "    n = len(a)\n"
            "    for i in range(n):\n"
            "        swapped = False\n"
            "        for j in range(0, n - i - 1):\n"
            "            if a[j] > a[j + 1]:\n"
            "                a[j], a[j + 1] = a[j + 1], a[j]\n"
            "                swapped = True\n"
            "        if not swapped:\n"
            "            break\n"
            "    return a\n"
        ),
    ),
    CodeVersionSeed(
        algorithm_slug="quick-sort",
        language="python",
        source_code=(
            "def quick_sort(arr: list[int]) -> list[int]:\n"
            "    if len(arr) <= 1:\n"
            "        return arr\n"
            "    pivot = arr[len(arr) // 2]\n"
            "    left = [x for x in arr if x < pivot]\n"
            "    middle = [x for x in arr if x == pivot]\n"
            "    right = [x for x in arr if x > pivot]\n"
            "    return quick_sort(left) + middle + quick_sort(right)\n"
        ),
    ),
    CodeVersionSeed(
        algorithm_slug="merge-sort",
        language="python",
        source_code=(
            "def merge_sort(arr: list[int]) -> list[int]:\n"
            "    if len(arr) <= 1:\n"
            "        return arr\n"
            "    mid = len(arr) // 2\n"
            "    left = merge_sort(arr[:mid])\n"
            "    right = merge_sort(arr[mid:])\n"
            "    return _merge(left, right)\n"
            "\n"
            "\n"
            "def _merge(left: list[int], right: list[int]) -> list[int]:\n"
            "    out: list[int] = []\n"
            "    i = j = 0\n"
            "    while i < len(left) and j < len(right):\n"
            "        if left[i] <= right[j]:\n"
            "            out.append(left[i])\n"
            "            i += 1\n"
            "        else:\n"
            "            out.append(right[j])\n"
            "            j += 1\n"
            "    out.extend(left[i:])\n"
            "    out.extend(right[j:])\n"
            "    return out\n"
        ),
    ),
    CodeVersionSeed(
        algorithm_slug="binary-search",
        language="python",
        source_code=(
            "def binary_search(arr: list[int], target: int) -> int:\n"
            "    lo, hi = 0, len(arr) - 1\n"
            "    while lo <= hi:\n"
            "        mid = (lo + hi) // 2\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        if arr[mid] < target:\n"
            "            lo = mid + 1\n"
            "        else:\n"
            "            hi = mid - 1\n"
            "    return -1\n"
        ),
    ),
    CodeVersionSeed(
        algorithm_slug="dijkstra",
        language="python",
        source_code=(
            "import heapq\n"
            "\n"
            "\n"
            "def dijkstra(\n"
            "    graph: dict[int, list[tuple[int, int]]], source: int\n"
            ") -> dict[int, int]:\n"
            "    dist: dict[int, int] = {source: 0}\n"
            "    pq: list[tuple[int, int]] = [(0, source)]\n"
            "    while pq:\n"
            "        d, u = heapq.heappop(pq)\n"
            "        if d > dist[u]:\n"
            "            continue\n"
            "        for v, w in graph[u]:\n"
            "            nd = d + w\n"
            "            if nd < dist.get(v, float(\"inf\")):\n"
            "                dist[v] = nd\n"
            "                heapq.heappush(pq, (nd, v))\n"
            "    return dist\n"
        ),
    ),
    CodeVersionSeed(
        algorithm_slug="bfs",
        language="python",
        source_code=(
            "from collections import deque\n"
            "\n"
            "\n"
            "def bfs(\n"
            "    graph: dict[int, list[int]], source: int\n"
            ") -> list[int]:\n"
            "    visited: list[int] = []\n"
            "    queue: deque[int] = deque([source])\n"
            "    seen = {source}\n"
            "    while queue:\n"
            "        u = queue.popleft()\n"
            "        visited.append(u)\n"
            "        for v in graph[u]:\n"
            "            if v not in seen:\n"
            "                seen.add(v)\n"
            "                queue.append(v)\n"
            "    return visited\n"
        ),
    ),
    CodeVersionSeed(
        algorithm_slug="dfs",
        language="python",
        source_code=(
            "def dfs(\n"
            "    graph: dict[int, list[int]], source: int\n"
            ") -> list[int]:\n"
            "    visited: list[int] = []\n"
            "    stack: list[int] = [source]\n"
            "    seen = {source}\n"
            "    while stack:\n"
            "        u = stack.pop()\n"
            "        visited.append(u)\n"
            "        for v in graph[u]:\n"
            "            if v not in seen:\n"
            "                seen.add(v)\n"
            "                stack.append(v)\n"
            "    return visited\n"
        ),
    ),
    CodeVersionSeed(
        algorithm_slug="fibonacci",
        language="python",
        source_code=(
            "from functools import lru_cache\n"
            "\n"
            "\n"
            "@lru_cache(maxsize=None)\n"
            "def fib(n: int) -> int:\n"
            "    if n < 2:\n"
            "        return n\n"
            "    return fib(n - 1) + fib(n - 2)\n"
        ),
    ),
    CodeVersionSeed(
        algorithm_slug="knapsack-01",
        language="python",
        source_code=(
            "def knapsack_01(\n"
            "    weights: list[int],\n"
            "    values: list[int],\n"
            "    capacity: int,\n"
            ") -> int:\n"
            "    n = len(weights)\n"
            "    dp = [[0] * (capacity + 1) for _ in range(n + 1)]\n"
            "    for i in range(1, n + 1):\n"
            "        for w in range(capacity + 1):\n"
            "            dp[i][w] = dp[i - 1][w]\n"
            "            if weights[i - 1] <= w:\n"
            "                cand = dp[i - 1][w - weights[i - 1]] + values[i - 1]\n"
            "                if cand > dp[i][w]:\n"
            "                    dp[i][w] = cand\n"
            "    return dp[n][capacity]\n"
        ),
    ),
    CodeVersionSeed(
        algorithm_slug="activity-selection",
        language="python",
        source_code=(
            "def activity_selection(\n"
            "    starts: list[int], finishes: list[int]\n"
            ") -> list[int]:\n"
            "    order = sorted(range(len(starts)), key=lambda i: finishes[i])\n"
            "    chosen: list[int] = [order[0]]\n"
            "    last_finish = finishes[order[0]]\n"
            "    for i in order[1:]:\n"
            "        if starts[i] >= last_finish:\n"
            "            chosen.append(i)\n"
            "            last_finish = finishes[i]\n"
            "    return chosen\n"
        ),
    ),
    CodeVersionSeed(
        algorithm_slug="karatsuba",
        language="python",
        source_code=(
            "def karatsuba(x: int, y: int) -> int:\n"
            "    if x < 10 or y < 10:\n"
            "        return x * y\n"
            "    n = max(len(str(x)), len(str(y)))\n"
            "    half = n // 2\n"
            "    base = 10 ** half\n"
            "    a, b = divmod(x, base)\n"
            "    c, d = divmod(y, base)\n"
            "    ac = karatsuba(a, c)\n"
            "    bd = karatsuba(b, d)\n"
            "    abcd = karatsuba(a + b, c + d)\n"
            "    return ac * 10 ** (2 * half) + (abcd - ac - bd) * base + bd\n"
        ),
    ),
    CodeVersionSeed(
        algorithm_slug="kmp",
        language="python",
        source_code=(
            "def kmp(text: str, pattern: str) -> list[int]:\n"
            "    if not pattern:\n"
            "        return []\n"
            "    # Build the failure function.\n"
            "    lps = [0] * len(pattern)\n"
            "    length = 0\n"
            "    for i in range(1, len(pattern)):\n"
            "        while length > 0 and pattern[length] != pattern[i]:\n"
            "            length = lps[length - 1]\n"
            "        if pattern[length] == pattern[i]:\n"
            "            length += 1\n"
            "        lps[i] = length\n"
            "    # Walk the text.\n"
            "    hits: list[int] = []\n"
            "    j = 0\n"
            "    for i, ch in enumerate(text):\n"
            "        while j > 0 and pattern[j] != ch:\n"
            "            j = lps[j - 1]\n"
            "        if pattern[j] == ch:\n"
            "            j += 1\n"
            "        if j == len(pattern):\n"
            "            hits.append(i - j + 1)\n"
            "            j = lps[j - 1]\n"
            "    return hits\n"
        ),
    ),
    CodeVersionSeed(
        algorithm_slug="inorder-traversal",
        language="python",
        source_code=(
            "class Node:\n"
            "    __slots__ = (\"val\", \"left\", \"right\")\n"
            "\n"
            "    def __init__(\n"
            "        self,\n"
            "        val: int,\n"
            "        left: \"Node | None\" = None,\n"
            "        right: \"Node | None\" = None,\n"
            "    ) -> None:\n"
            "        self.val = val\n"
            "        self.left = left\n"
            "        self.right = right\n"
            "\n"
            "\n"
            "def inorder(root: Node | None) -> list[int]:\n"
            "    out: list[int] = []\n"
            "    stack: list[Node] = []\n"
            "    cur = root\n"
            "    while cur or stack:\n"
            "        while cur:\n"
            "            stack.append(cur)\n"
            "            cur = cur.left\n"
            "        cur = stack.pop()\n"
            "        out.append(cur.val)\n"
            "        cur = cur.right\n"
            "    return out\n"
        ),
    ),
)


__all__ = ["CODE_VERSIONS", "CodeVersionSeed"]
