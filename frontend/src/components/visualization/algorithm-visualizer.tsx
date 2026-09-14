"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { CodePanel, type SourceLanguage } from "@/components/visualization/code-panel";
import { ComplexityPanel } from "@/components/visualization/complexity-panel";
import { CurrentStepPanel } from "@/components/visualization/current-step-panel";
import { VisualizationCanvas } from "@/components/visualization/visualization-canvas";
import { VisualizationControls } from "@/components/visualization/visualization-controls";
import { ArrayAdapter } from "@/features/visualization/adapters/array-adapter";
import { reportAlgorithmCompletionBySlug } from "@/lib/api/progress";
import { StepScheduler } from "@/features/visualization/player/step-scheduler";
import type { ArrayAlgorithmModule } from "@/features/visualization/modules/types";
import { useEngineStore } from "@/stores/engine-store";

export interface AlgorithmVisualizerProps {
  module: ArrayAlgorithmModule<number[]>;
  sources: Record<SourceLanguage, string>;
}

export function AlgorithmVisualizer({ module, sources }: AlgorithmVisualizerProps) {
  const [language, setLanguage] = useState<SourceLanguage>("typescript");
  const store = useEngineStore();
  const load = useEngineStore((state) => state.load);
  const scheduler = useRef<StepScheduler | null>(null);
  const reportedSessions = useRef(new Set<string>());

  useEffect(() => {
    load(module, module.defaultInput());
  }, [load, module]);

  useEffect(() => {
    scheduler.current = new StepScheduler({
      getDelay: () => useEngineStore.getState().speed,
      onStep: () => useEngineStore.getState().stepEnd(),
      shouldContinue: () => useEngineStore.getState().status === "playing",
    });
    return () => scheduler.current?.dispose();
  }, []);

  useEffect(() => {
    if (store.status === "playing") scheduler.current?.play();
    else scheduler.current?.pause();
  }, [store.status]);

  useEffect(() => {
    if (
      store.status !== "complete" ||
      !store.sessionId ||
      reportedSessions.current.has(store.sessionId)
    )
      return;
    reportedSessions.current.add(store.sessionId);
    void reportAlgorithmCompletionBySlug(module.slug).catch(() => undefined);
  }, [module.slug, store.sessionId, store.status]);

  const currentEvent = store.status === "idle" ? undefined : store.events[store.currentStep];
  const state = useMemo(() => {
    const initial = ArrayAdapter.createInitialState(module.defaultInput());
    const appliedEvents =
      store.status === "idle" ? [] : store.events.slice(0, store.currentStep + 1);
    return appliedEvents.reduce(ArrayAdapter.reduce, initial);
  }, [module, store.currentStep, store.events, store.status]);

  return (
    <div className="space-y-6">
      <VisualizationCanvas adapterKind="array" state={state} />
      <div aria-label="Array values" className="flex flex-wrap gap-2">
        {state.items.map((item) => (
          <span
            className="rounded-md border border-border bg-surface px-3 py-2 font-mono text-foreground"
            key={item.id}
          >
            {String(item.value)}
          </span>
        ))}
      </div>
      <VisualizationControls
        canNext={store.currentStep < store.events.length - 1 && store.status !== "complete"}
        canPrev={store.currentStep > 0}
        onNext={store.next}
        onPause={store.pause}
        onPlay={store.play}
        onPrev={store.prev}
        onReset={store.reset}
        onSeek={store.seek}
        onSpeedChange={(speed) => store.setSpeed(speed as typeof store.speed)}
        speed={store.speed}
        status={store.status}
      />
      <CurrentStepPanel
        currentStep={store.currentStep}
        totalSteps={store.events.length}
        {...(currentEvent ? { message: currentEvent.message } : {})}
      />
      <CodePanel
        language={language}
        onLanguageChange={setLanguage}
        sources={sources}
        {...(currentEvent?.line === undefined ? {} : { currentLine: currentEvent.line })}
      />
      <ComplexityPanel complexity={module.meta.complexity} />
    </div>
  );
}
