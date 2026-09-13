import type { AlgorithmEvent, AlgorithmEventDraft } from "@/features/visualization/events";
import { assertBinarySearchTree, uniqueNodeId } from "@/features/visualization/modules/bst/tree";
import type { TreeNode, RunOptions } from "@/features/visualization/modules/types";

export const DEFAULT_INSERT_VALUE = 7;

function withLine<Event extends AlgorithmEventDraft>(
  event: Event,
  line: number,
  options?: RunOptions,
) {
  return options?.highlightLines === false ? event : { ...event, line };
}

export function run(root: TreeNode | null, options?: RunOptions): AlgorithmEvent[] {
  assertBinarySearchTree(root);
  const value = options?.target ?? DEFAULT_INSERT_VALUE;
  if (!Number.isFinite(value)) throw new TypeError("BST Insert requires a finite value.");

  const events: AlgorithmEvent[] = [];
  let step = 0;
  const emit = (event: AlgorithmEventDraft) => {
    events.push({ ...event, id: `bst-insert-${step}`, t: step });
    step += 1;
  };

  if (root === null) {
    const elementId = uniqueNodeId(root, value);
    emit(
      withLine(
        { type: "insert", elementId, value, message: `Inserting ${value} as the root.` },
        3,
        options,
      ),
    );
    emit(
      withLine(
        { type: "mark", elementId, status: "visited", message: `${value} is the root node.` },
        14,
        options,
      ),
    );
    emit(
      withLine(
        { type: "complete", message: "Insertion complete.", summary: { inserted: true, value } },
        15,
        options,
      ),
    );
    return events;
  }

  let current = root;
  while (true) {
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
          message: `Comparing ${value} with ${current.value}.`,
        },
        6,
        options,
      ),
    );
    if (value === current.value) {
      emit(
        withLine(
          { type: "found", ids: [current.id], message: `${value} already exists in the tree.` },
          7,
          options,
        ),
      );
      emit(
        withLine(
          { type: "complete", message: "Insertion complete.", summary: { inserted: false, value } },
          15,
          options,
        ),
      );
      return events;
    }

    const position = value < current.value ? "left" : "right";
    const next = current[position];
    if (next !== null) {
      emit(
        withLine(
          {
            type: "visit",
            elementId: current.id,
            message: `Moving ${position} from ${current.value}.`,
          },
          9,
          options,
        ),
      );
      current = next;
      continue;
    }

    const elementId = uniqueNodeId(root, value);
    emit(
      withLine(
        {
          type: "insert",
          elementId,
          parentId: current.id,
          position,
          value,
          message: `Inserting ${value} to the ${position} of ${current.value}.`,
        },
        12,
        options,
      ),
    );
    emit(
      withLine(
        { type: "mark", elementId, status: "visited", message: `${value} is now a leaf node.` },
        14,
        options,
      ),
    );
    emit(
      withLine(
        { type: "complete", message: "Insertion complete.", summary: { inserted: true, value } },
        15,
        options,
      ),
    );
    return events;
  }
}
