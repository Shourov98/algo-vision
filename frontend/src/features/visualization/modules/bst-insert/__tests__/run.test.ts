import { describe, expect, it } from "vitest";

import { TreeAdapter } from "@/features/visualization/adapters/tree-adapter";
import { createDefaultBst } from "@/features/visualization/modules/bst/tree";
import {
  CANONICAL_EVENT_COUNT,
  CANONICAL_INSERT_VALUE,
} from "@/features/visualization/modules/bst-insert/__tests__/canonical/trace";
import { run } from "@/features/visualization/modules/bst-insert/run";

describe("bst-insert/run", () => {
  it("produces the locked canonical trace", () => {
    expect(run(createDefaultBst(), { target: CANONICAL_INSERT_VALUE })).toHaveLength(
      CANONICAL_EVENT_COUNT,
    );
  });

  it("is deterministic and inserts a structural leaf without mutating the input", () => {
    const root = createDefaultBst();
    const events = run(root, { target: CANONICAL_INSERT_VALUE });
    const state = events.reduce(TreeAdapter.reduce, TreeAdapter.createInitialState(root));

    expect(run(root, { target: CANONICAL_INSERT_VALUE })).toEqual(events);
    expect(root.left?.right?.right).toBeNull();
    expect(state.nodes.find((node) => node.id === "node-6")?.rightId).toBe("node-7");
    expect(state.nodes.find((node) => node.id === "node-7")?.value).toBe(7);
  });

  it("reports duplicates without adding another node", () => {
    const events = run(createDefaultBst(), { target: 6 });
    const complete = events.at(-1);
    if (!complete || complete.type !== "complete") throw new Error("Expected complete event.");

    expect(events.some((event) => event.type === "insert")).toBe(false);
    expect(complete.summary).toEqual({ inserted: false, value: 6 });
  });
});
