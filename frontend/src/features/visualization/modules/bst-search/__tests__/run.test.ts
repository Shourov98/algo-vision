import { describe, expect, it } from "vitest";

import { TreeAdapter } from "@/features/visualization/adapters/tree-adapter";
import { createDefaultBst } from "@/features/visualization/modules/bst/tree";
import {
  CANONICAL_EVENT_COUNT,
  CANONICAL_TARGET,
} from "@/features/visualization/modules/bst-search/__tests__/canonical/trace";
import { run } from "@/features/visualization/modules/bst-search/run";

describe("bst-search/run", () => {
  it("produces the locked canonical trace", () => {
    expect(run(createDefaultBst(), { target: CANONICAL_TARGET })).toHaveLength(
      CANONICAL_EVENT_COUNT,
    );
  });

  it("is deterministic and marks the discovered tree node", () => {
    const root = createDefaultBst();
    const events = run(root, { target: CANONICAL_TARGET });
    const state = events.reduce(TreeAdapter.reduce, TreeAdapter.createInitialState(root));

    expect(run(root, { target: CANONICAL_TARGET })).toEqual(events);
    expect(state.nodes.find((node) => node.id === "node-6")?.status).toBe("found");
  });

  it("completes a missing search and rejects malformed BST ordering", () => {
    const events = run(createDefaultBst(), { target: 5 });
    const complete = events.at(-1);
    if (!complete || complete.type !== "complete") throw new Error("Expected complete event.");

    expect(events.some((event) => event.type === "found")).toBe(false);
    expect(complete.summary).toEqual({ found: false, target: 5 });
    expect(() =>
      run({
        id: "root",
        value: 2,
        left: null,
        right: { id: "bad", value: 1, left: null, right: null },
      }),
    ).toThrow(/strictly ordered/);
  });
});
