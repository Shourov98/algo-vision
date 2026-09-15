"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { CodePanel, type SourceLanguage } from "@/components/visualization/code-panel";
import { ArrayInputPanel } from "@/components/visualization/array-input-panel";
import { ArrayVisualization } from "@/components/visualization/array-visualization";
import { ComplexityPanel } from "@/components/visualization/complexity-panel";
import { CurrentStepPanel } from "@/components/visualization/current-step-panel";
import { VisualizationControls } from "@/components/visualization/visualization-controls";
import { ArrayAdapter } from "@/features/visualization/adapters/array-adapter";
import type { ArrayRunConfiguration } from "@/features/visualization/array-run-configuration";
import type { AlgorithmEvent } from "@/features/visualization/events";
import { reportAlgorithmCompletionBySlug } from "@/lib/api/progress";
import { StepScheduler } from "@/features/visualization/player/step-scheduler";
import type { ArrayAlgorithmModule } from "@/features/visualization/modules/types";
import { useEngineStore } from "@/stores/engine-store";

export interface AlgorithmVisualizerProps {
  module: ArrayAlgorithmModule<number[]>;
  sources: Record<SourceLanguage, string>;
}

const EMPTY_EVENTS: AlgorithmEvent[] = [];

function createConfiguration(module: ArrayAlgorithmModule<number[]>): ArrayRunConfiguration {
  const values = module.defaultInput();
  return {
    direction: "ascending",
    ...(module.capabilities.supportsTarget
      ? { target: values[Math.floor(values.length / 2)] }
      : {}),
    values,
  };
}

export function AlgorithmVisualizer({ module, sources }: AlgorithmVisualizerProps) {
  return <AlgorithmVisualizerInstance key={module.slug} module={module} sources={sources} />;
}

function AlgorithmVisualizerInstance({ module, sources }: AlgorithmVisualizerProps) {
  const [language, setLanguage] = useState<SourceLanguage>("typescript");
  const [configuration, setConfiguration] = useState(() => createConfiguration(module));
  const store = useEngineStore();
  const load = useEngineStore((state) => state.load);
  const scheduler = useRef<StepScheduler | null>(null);
  const reportedSessions = useRef(new Set<string>());
  const isCurrentModule = store.slug === module.slug;
  const events = isCurrentModule ? store.events : EMPTY_EVENTS;
  const currentStep = isCurrentModule ? store.currentStep : 0;
  const status = isCurrentModule ? store.status : "idle";

  useEffect(() => {
    const nextConfiguration = createConfiguration(module);
    load(module, nextConfiguration.values, nextConfiguration);
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
    if (status === "playing") scheduler.current?.play();
    else scheduler.current?.pause();
  }, [status]);

  useEffect(() => {
    if (
      !isCurrentModule ||
      status !== "complete" ||
      !store.sessionId ||
      reportedSessions.current.has(store.sessionId)
    )
      return;
    reportedSessions.current.add(store.sessionId);
    void reportAlgorithmCompletionBySlug(module.slug).catch(() => undefined);
  }, [isCurrentModule, module.slug, status, store.sessionId]);

  const currentEvent = status === "idle" ? undefined : events[currentStep];
  const input =
    isCurrentModule && Array.isArray(store.visualizationState)
      ? store.visualizationState
      : configuration.values;
  const state = useMemo(() => {
    const initial = ArrayAdapter.createInitialState(input);
    const appliedEvents = status === "idle" ? [] : events.slice(0, currentStep + 1);
    return appliedEvents.reduce(ArrayAdapter.reduce, initial);
  }, [currentStep, events, input, status]);

  return (
    <div className="space-y-6">
      <ArrayInputPanel
        capabilities={module.capabilities}
        configuration={configuration}
        onChange={setConfiguration}
        onStart={() => load(module, configuration.values, configuration)}
      />
      <ArrayVisualization
        state={state}
        stepDuration={store.speed}
        {...(currentEvent ? { currentEvent } : {})}
      />
      <VisualizationControls
        canNext={currentStep < events.length - 1 && status !== "complete"}
        canPrev={currentStep > 0}
        currentStep={currentStep}
        onNext={store.next}
        onPause={store.pause}
        onPlay={store.play}
        onPrev={store.prev}
        onReset={store.reset}
        onSeek={store.seek}
        onSpeedChange={(speed) => store.setSpeed(speed as typeof store.speed)}
        speed={store.speed}
        status={status}
        totalSteps={events.length}
      />
      <CurrentStepPanel
        currentStep={currentStep}
        {...(currentEvent ? { metadata: { action: currentEvent.type } } : {})}
        totalSteps={events.length}
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
