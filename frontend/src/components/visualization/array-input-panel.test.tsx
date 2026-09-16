import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ArrayInputPanel } from "@/components/visualization/array-input-panel";
import { binarySearchModule } from "@/features/visualization/modules/binary-search";

describe("ArrayInputPanel", () => {
  it("announces pending changes and explicitly sorts before starting Binary Search", () => {
    const onChange = vi.fn();
    const onSortAndStart = vi.fn();
    render(
      <ArrayInputPanel
        capabilities={binarySearchModule.capabilities}
        configuration={{ direction: "ascending", target: 7, values: [5, 1, 7] }}
        hasPendingChanges
        onChange={onChange}
        onSortAndStart={onSortAndStart}
        onStart={vi.fn()}
      />,
    );

    expect(screen.getByText("Next run setup")).toBeInTheDocument();
    expect(screen.getByText(/Changes have not been applied/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Start over" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Sort ascending & start" }));
    expect(onSortAndStart).toHaveBeenCalledWith({
      direction: "ascending",
      target: 7,
      values: [1, 5, 7],
    });
  });
});
