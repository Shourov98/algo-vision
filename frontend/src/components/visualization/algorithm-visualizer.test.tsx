import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AlgorithmVisualizer } from "@/components/visualization/algorithm-visualizer";
import { bubbleSortModule } from "@/features/visualization/modules/bubble-sort";
import { bubbleSortCpp } from "@/features/visualization/modules/bubble-sort/code/cpp";
import { bubbleSortPython } from "@/features/visualization/modules/bubble-sort/code/python";
import { bubbleSortTypeScript } from "@/features/visualization/modules/bubble-sort/code/typescript";
import { mergeSortModule } from "@/features/visualization/modules/merge-sort";
import { useEngineStore } from "@/stores/engine-store";

describe("AlgorithmVisualizer", () => {
  it("loads Bubble Sort and advances the rendered array through controls", async () => {
    render(
      <AlgorithmVisualizer
        module={bubbleSortModule}
        sources={{ cpp: bubbleSortCpp, python: bubbleSortPython, typescript: bubbleSortTypeScript }}
      />,
    );

    await waitFor(() => expect(screen.getByLabelText("Value 5 at index 0")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    await waitFor(() =>
      expect(screen.getByLabelText("Value 2 at index 0, active")).toBeInTheDocument(),
    );
  });

  it("does not apply a previous algorithm trace while a new module is loading", () => {
    useEngineStore.getState().load(mergeSortModule, mergeSortModule.defaultInput());
    useEngineStore.getState().seek(10);

    let container: HTMLElement | undefined;
    expect(() => {
      ({ container } = render(
        <AlgorithmVisualizer
          module={bubbleSortModule}
          sources={{
            cpp: bubbleSortCpp,
            python: bubbleSortPython,
            typescript: bubbleSortTypeScript,
          }}
        />,
      ));
    }).not.toThrow();

    expect(container?.querySelector('[aria-label="Value 5 at index 0"]')).toBeInTheDocument();
  });
});
