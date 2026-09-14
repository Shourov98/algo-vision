export const bubbleSortTypeScript = `function bubbleSort(values: number[]): number[] {
  const items = values.slice();

  for (let pass = 0; pass < items.length - 1; pass += 1) {
    for (let index = 0; index < items.length - pass - 1; index += 1) {
      if (items[index]! > items[index + 1]!) {
        [items[index], items[index + 1]] = [items[index + 1]!, items[index]!];
      }
    }
  }

  return items;
}`;
