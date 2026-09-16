import { describe, expect, it } from "vitest";

import { ArrayAdapter } from "@/features/visualization/adapters/array-adapter";
import { run } from "@/features/visualization/modules/binary-search/run";
import {
  CANONICAL_EVENT_COUNT,
  CANONICAL_INPUT,
  CANONICAL_TARGET,
} from "@/features/visualization/modules/binary-search/__tests__/canonical/trace";

describe("binary-search/run", () => {
  it("produces the locked canonical trace", () => {
    expect(run([...CANONICAL_INPUT], { target: CANONICAL_TARGET })).toHaveLength(
      CANONICAL_EVENT_COUNT,
    );
  });

  it("is deterministic, finds the target, and preserves the input", () => {
    const input = [...CANONICAL_INPUT];
    const events = run(input, { target: CANONICAL_TARGET });
    const finalState = events.reduce(ArrayAdapter.reduce, ArrayAdapter.createInitialState(input));

    expect(run(input, { target: CANONICAL_TARGET })).toEqual(events);
    expect(input).toEqual(CANONICAL_INPUT);
    expect(events.map((event) => event.id)).toEqual(
      events.map((_, index) => `binary-search-${index}`),
    );
    expect(finalState.items[3]?.status).toBe("found");
    const complete = events.at(-1);
    if (!complete || complete.type !== "complete") throw new Error("Expected complete event.");
    expect(complete.summary).toEqual({ found: true, index: 3, target: 7 });
  });

  it("finishes with an absent-target result and rejects unsorted input", () => {
    const events = run([...CANONICAL_INPUT], { target: 8 });
    const complete = events.at(-1);
    if (!complete || complete.type !== "complete") throw new Error("Expected complete event.");

    expect(events.some((event) => event.type === "found")).toBe(false);
    expect(complete.summary).toEqual({ found: false, index: -1, target: 8 });
    expect(() => run([3, 1], { target: 1 })).toThrow(/ascending order/);
  });

  it("finds a target in descending order", () => {
    const input = [11, 9, 7, 5, 3, 1];
    const events = run(input, { direction: "descending", target: 7 });
    const complete = events.at(-1);

    if (!complete || complete.type !== "complete") throw new Error("Expected complete event.");
    expect(complete.summary).toEqual({ found: true, index: 2, target: 7 });
  });

  it("emits stable search ranges and direction-aware decisions", () => {
    const events = run([...CANONICAL_INPUT], { target: CANONICAL_TARGET });
    const ranges = events.filter((event) => event.type === "search-range");

    expect(ranges).toHaveLength(3);
    expect(ranges[0]).toMatchObject({
      activeIds: ["element-1", "element-2", "element-3", "element-4", "element-5", "element-6"],
      highId: "element-6",
      lowId: "element-1",
      middleId: "element-3",
      target: 7,
    });
    expect(events.some((event) => event.message.includes("discard the left half"))).toBe(true);
  });

  it("retains all exclusions when a descending search does not find its target", () => {
    const events = run([11, 9, 7, 5, 3, 1], { direction: "descending", target: 8 });
    const finalRange = events.filter((event) => event.type === "search-range").at(-1);

    expect(finalRange).toMatchObject({
      activeIds: [],
      eliminatedIds: ["element-1", "element-2", "element-3", "element-4", "element-5", "element-6"],
      target: 8,
    });
    expect(events.some((event) => event.message.includes("discard the right half"))).toBe(true);
  });
});
