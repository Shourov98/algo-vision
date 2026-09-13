export const binarySearchTypeScript = `function binarySearch(values: number[], target: number): number {
  let low = 0;
  let high = values.length - 1;

  while (low <= high) {
    const middle = low + Math.floor((high - low) / 2);
    const candidate = values[middle]!;
    if (candidate === target) return middle;

    if (candidate < target) low = middle + 1;
    else high = middle - 1;
  }

  return -1;
}`;
