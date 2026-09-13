import { describe, expect, it } from "vitest";

import { TreeAdapter } from "@/features/visualization/adapters/tree-adapter";
import { EngineInvariantError } from "@/features/visualization/errors";
import type { TreeNode } from "@/features/visualization/modules/types";

const tree: TreeNode = {
  id: "root",
  value: 8,
  left: { id: "left", value: 3, left: null, right: null },
  right: { id: "right", value: 10, left: null, right: null },
};

describe("TreeAdapter", () => {
  it("creates a stable, independent tree state", () => {
    const state = TreeAdapter.createInitialState(tree);

    expect(state).toEqual({
      rootId: "root",
      nodes: [
        { id: "root", value: 8, status: "idle", leftId: "left", rightId: "right" },
        { id: "left", value: 3, status: "idle", leftId: null, rightId: null },
        { id: "right", value: 10, status: "idle", leftId: null, rightId: null },
      ],
    });
    expect(TreeAdapter.getElementIds(state)).toEqual(["root", "left", "right"]);
    expect(TreeAdapter.getElement(state, "left")?.value).toBe(3);
  });

  it("reduces node statuses without mutating the previous state", () => {
    const initial = TreeAdapter.createInitialState(tree);
    const next = TreeAdapter.reduce(initial, {
      id: "event-1",
      t: 1,
      type: "found",
      ids: ["left"],
      message: "Found 3.",
    });

    expect(initial.nodes[1]?.status).toBe("idle");
    expect(next.nodes[1]?.status).toBe("found");
    expect(next).not.toBe(initial);
  });

  it("inserts and deletes leaf nodes while preserving parent links", () => {
    const initial = TreeAdapter.createInitialState(tree);
    const inserted = TreeAdapter.reduce(initial, {
      id: "event-1",
      t: 1,
      type: "insert",
      elementId: "left-left",
      parentId: "left",
      position: "left",
      value: 1,
      message: "Insert 1.",
    });
    const deleted = TreeAdapter.reduce(inserted, {
      id: "event-2",
      t: 2,
      type: "delete",
      elementId: "left-left",
      message: "Delete 1.",
    });

    expect(inserted.nodes.find((node) => node.id === "left")?.leftId).toBe("left-left");
    expect(deleted.nodes.find((node) => node.id === "left")?.leftId).toBeNull();
    expect(TreeAdapter.getElement(deleted, "left-left")).toBeUndefined();
  });

  it("rejects malformed trees and invalid structural transitions", () => {
    expect(() => TreeAdapter.createInitialState({ ...tree, right: { ...tree.left } })).toThrow(
      EngineInvariantError,
    );
    expect(() =>
      TreeAdapter.reduce(TreeAdapter.createInitialState(tree), {
        id: "event-1",
        t: 1,
        type: "insert",
        elementId: "another-left",
        parentId: "root",
        position: "left",
        value: 2,
        message: "Insert 2.",
      }),
    ).toThrow(/already has a left child/);
  });
});
