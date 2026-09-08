import { create } from "zustand";

export interface UIStore {
  isCodePanelOpen: boolean;
  isExplanationOpen: boolean;
  isCompactLayout: boolean;
  toggleCodePanel(): void;
  toggleExplanationPanel(): void;
  setCompactLayout(compact: boolean): void;
}

export const useUIStore = create<UIStore>()((set) => ({
  isCodePanelOpen: true,
  isExplanationOpen: true,
  isCompactLayout: false,
  toggleCodePanel: () => set((state) => ({ isCodePanelOpen: !state.isCodePanelOpen })),
  toggleExplanationPanel: () => set((state) => ({ isExplanationOpen: !state.isExplanationOpen })),
  setCompactLayout: (isCompactLayout) => set({ isCompactLayout }),
}));

export const useCodePanelOpen = () => useUIStore((state) => state.isCodePanelOpen);
export const useExplanationPanelOpen = () => useUIStore((state) => state.isExplanationOpen);
