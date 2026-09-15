export const mergeSortTypeScript = `function mergeSort(values: number[]): number[] {
  if (values.length <= 1) return values;

  const middle = Math.floor(values.length / 2);
  const left = mergeSort(values.slice(0, middle));
  const right = mergeSort(values.slice(middle));
  return merge(left, right);
}

function merge(left: number[], right: number[]): number[] {
  const result: number[] = [];
  while (left.length && right.length) {
    result.push(left[0] <= right[0] ? left.shift()! : right.shift()!);
  }
  return [...result, ...left, ...right];
}`;
