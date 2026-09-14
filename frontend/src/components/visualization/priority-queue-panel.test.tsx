import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PriorityQueuePanel } from "@/components/visualization/priority-queue-panel";
describe("PriorityQueuePanel", () => {
  it("orders entries by priority", () => {
    render(
      <PriorityQueuePanel
        entries={[
          { id: "b", priority: 3 },
          { id: "a", priority: 1 },
        ]}
      />,
    );
    expect(screen.getByRole("list").textContent).toBe("a1b3");
  });
});
