export interface StepSchedulerOptions {
  getDelay(): number;
  onStep(): void;
  shouldContinue(): boolean;
}

export class StepScheduler {
  private timer: ReturnType<typeof setTimeout> | undefined;

  constructor(private readonly options: StepSchedulerOptions) {}

  play() {
    if (this.timer !== undefined) return;
    this.schedule();
  }

  pause() {
    this.cancel();
  }

  seek() {
    this.cancel();
  }

  reset() {
    this.cancel();
  }

  dispose() {
    this.cancel();
  }

  private schedule() {
    this.timer = setTimeout(() => {
      this.timer = undefined;
      this.options.onStep();
      if (this.options.shouldContinue()) this.schedule();
    }, this.options.getDelay());
  }

  private cancel() {
    if (this.timer === undefined) return;
    clearTimeout(this.timer);
    this.timer = undefined;
  }
}
