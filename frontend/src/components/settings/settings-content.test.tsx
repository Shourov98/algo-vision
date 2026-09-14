import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { SettingsContent } from "@/components/settings/settings-content";
import { useUIStore } from "@/stores/ui-store";
describe("SettingsContent", () => {
  beforeEach(() =>
    useUIStore.setState({ isCodePanelOpen: true, isCompactLayout: false, isExplanationOpen: true }),
  );
  it("updates compact layout preference", () => {
    render(<SettingsContent />);
    const input = screen.getByLabelText("Use compact visualization layout");
    expect(input).not.toBeChecked();
    input.click();
    expect(useUIStore.getState().isCompactLayout).toBe(true);
  });
});
