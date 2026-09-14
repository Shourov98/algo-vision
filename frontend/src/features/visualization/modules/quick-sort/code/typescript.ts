export const quickSortTypeScript = `function quickSort(values: number[]): number[] {
  if (values.length <= 1) return values;
  const pivot = values.at(-1)!;
  const smaller = values.slice(0, -1).filter((value) => value <= pivot);
  const larger = values.slice(0, -1).filter((value) => value > pivot);
  return [...quickSort(smaller), pivot, ...quickSort(larger)];
}`;
