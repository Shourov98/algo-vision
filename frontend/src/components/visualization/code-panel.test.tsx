import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { CodePanel } from "@/components/visualization/code-panel";

const sources = {
  cpp: "line one\nline two",
  python: "line one\nline two",
  typescript: "line one\nline two",
};

describe("CodePanel", () => {
  it("highlights the supplied source line and changes languages", () => {
    const onLanguageChange = vi.fn();
    render(
      <CodePanel
        currentLine={2}
        language="typescript"
        onLanguageChange={onLanguageChange}
        sources={sources}
      />,
    );

    expect(screen.getByText("line two").parentElement).toHaveAttribute("data-current", "true");
    fireEvent.click(screen.getByRole("tab", { name: "Python" }));
    expect(onLanguageChange).toHaveBeenCalledWith("python");
  });
});
