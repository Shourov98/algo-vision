import type { AlgorithmEvent, AlgorithmEventDraft } from "@/features/visualization/events";
import { assertBinarySearchTree } from "@/features/visualization/modules/bst/tree";
import type { TreeNode, RunOptions } from "@/features/visualization/modules/types";

export const DEFAULT_TARGET = 6;

function withLine<Event extends AlgorithmEventDraft>(
  event: Event,
  line: number,
  options?: RunOptions,
) {
  return options?.highlightLines === false ? event : { ...event, line };
}

export function run(root: TreeNode | null, options?: RunOptions): AlgorithmEvent[] {
  assertBinarySearchTree(root);
  const target = options?.target ?? DEFAULT_TARGET;
  if (!Number.isFinite(target)) throw new TypeError("BST Search requires a finite target.");

  const events: AlgorithmEvent[] = [];
  let step = 0;
  const emit = (event: AlgorithmEventDraft) => {
    events.push({ ...event, id: `bst-search-${step}`, t: step });
    step += 1;
  };

  let current = root;
  while (current !== null) {
    emit(
      withLine(
        {
          type: "mark",
          elementId: current.id,
          status: "current",
          message: `Checking node ${current.value}.`,
        },
        5,
        options,
      ),
    );
    emit(
      withLine(
        {
          type: "compare",
          ids: [current.id],
          message: `Comparing ${target} with ${current.value}.`,
        },
        6,
        options,
      ),
    );
    if (target === current.value) {
      emit(withLine({ type: "found", ids: [current.id], message: `Found ${target}.` }, 7, options));
      emit(
        withLine(
          { type: "complete", message: "Search complete.", summary: { found: true, target } },
          14,
          options,
        ),
      );
      return events;
    }

    const position = target < current.value ? "left" : "right";
    emit(
      withLine(
        {
          type: "visit",
          elementId: current.id,
          message: `Moving ${position} from ${current.value}.`,
        },
        10,
        options,
      ),
    );
    current = current[position];
  }

  emit(
    withLine(
      {
        type: "complete",
        message: `${target} is not in the tree.`,
        summary: { found: false, target },
      },
      14,
      options,
    ),
  );
  return events;
}
