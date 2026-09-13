import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AlgorithmVisualizer } from "@/components/visualization/algorithm-visualizer";
import { bubbleSortModule } from "@/features/visualization/modules/bubble-sort";
import { bubbleSortCpp } from "@/features/visualization/modules/bubble-sort/code/cpp";
import { bubbleSortPython } from "@/features/visualization/modules/bubble-sort/code/python";
import { bubbleSortTypeScript } from "@/features/visualization/modules/bubble-sort/code/typescript";

describe("AlgorithmVisualizer", () => {
  it("loads Bubble Sort and advances the rendered array through controls", async () => {
    render(
      <AlgorithmVisualizer
        module={bubbleSortModule}
        sources={{ cpp: bubbleSortCpp, python: bubbleSortPython, typescript: bubbleSortTypeScript }}
      />,
    );

    await waitFor(() => expect(screen.getByLabelText("Array values")).toHaveTextContent("52814"));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    await waitFor(() => expect(screen.getByLabelText("Array values")).toHaveTextContent("25814"));
  });
});
