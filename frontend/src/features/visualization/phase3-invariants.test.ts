import { describe, expect, it } from "vitest";

import { HeapAdapter } from "@/features/visualization/adapters/heap-adapter";
import { TreeAdapter } from "@/features/visualization/adapters/tree-adapter";
import { createDefaultBst } from "@/features/visualization/modules/bst/tree";
import { run as runBstInsert } from "@/features/visualization/modules/bst-insert/run";
import { run as runBstSearch } from "@/features/visualization/modules/bst-search/run";
import { run as runHeapSort } from "@/features/visualization/modules/heap-sort/run";
import {
  runInOrder,
  runPostOrder,
  runPreOrder,
} from "@/features/visualization/modules/tree-traversals";

function expectTraceInvariant(events: ReturnType<typeof runHeapSort>) {
  expect(events.at(-1)?.type).toBe("complete");
  expect(events.map((event) => event.t)).toEqual(events.map((_, index) => index));
  expect(new Set(events.map((event) => event.id))).toHaveLength(events.length);
}

describe("Phase 3 visualization invariants", () => {
  it("keeps Heap Sort deterministic and produces sorted adapter state", () => {
    const input = [5, 2, 8, 1, 4];
    const events = runHeapSort(input);
    const state = events.reduce(HeapAdapter.reduce, HeapAdapter.createInitialState(input));

    expect(runHeapSort(input)).toEqual(events);
    expectTraceInvariant(events);
    expect(state.items.map((item) => item.value)).toEqual([1, 2, 4, 5, 8]);
    expect(state.heapSize).toBe(0);
  });

  it.each([
    ["BST insert", () => runBstInsert(createDefaultBst(), { target: 7 })],
    ["BST search", () => runBstSearch(createDefaultBst(), { target: 6 })],
    ["in-order", () => runInOrder(createDefaultBst())],
    ["pre-order", () => runPreOrder(createDefaultBst())],
    ["post-order", () => runPostOrder(createDefaultBst())],
  ])("keeps %s traces deterministic and complete", (_, createEvents) => {
    const events = createEvents();
    expect(createEvents()).toEqual(events);
    expectTraceInvariant(events);
  });

  it("reduces BST insertion and search without mutating the original tree state", () => {
    const root = createDefaultBst();
    const initial = TreeAdapter.createInitialState(root);
    const inserted = runBstInsert(root, { target: 7 }).reduce(TreeAdapter.reduce, initial);
    const searched = runBstSearch(root, { target: 6 }).reduce(TreeAdapter.reduce, initial);

    expect(initial.nodes).toHaveLength(6);
    expect(inserted.nodes.find((node) => node.id === "node-7")?.value).toBe(7);
    expect(searched.nodes.find((node) => node.id === "node-6")?.status).toBe("found");
  });
});
