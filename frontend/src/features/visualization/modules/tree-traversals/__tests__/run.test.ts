import { describe, expect, it } from "vitest";
import { TreeAdapter } from "@/features/visualization/adapters/tree-adapter";
import { createDefaultBst } from "@/features/visualization/modules/bst/tree";
import {
  IN_ORDER,
  POST_ORDER,
  PRE_ORDER,
} from "@/features/visualization/modules/tree-traversals/__tests__/canonical/trace";
import {
  runInOrder,
  runPostOrder,
  runPreOrder,
} from "@/features/visualization/modules/tree-traversals";

describe("tree traversals", () => {
  it.each([
    ["in-order", runInOrder, IN_ORDER],
    ["pre-order", runPreOrder, PRE_ORDER],
    ["post-order", runPostOrder, POST_ORDER],
  ] as const)("produces the canonical %s trace", (_, run, expected) => {
    const root = createDefaultBst();
    const events = run(root);
    expect(
      events
        .filter((event) => event.type === "visit")
        .map((event) => (event.type === "visit" ? event.elementId : "")),
    ).toEqual(expected);
    expect(run(root)).toEqual(events);
    expect(events.at(-1)?.type).toBe("complete");
  });

  it("reduces visits immutably through TreeAdapter", () => {
    const root = createDefaultBst();
    const initial = TreeAdapter.createInitialState(root);
    const final = runPostOrder(root).reduce(TreeAdapter.reduce, initial);
    expect(initial.nodes.every((node) => node.status === "idle")).toBe(true);
    expect(final.nodes.every((node) => node.status === "visited")).toBe(true);
  });
});
