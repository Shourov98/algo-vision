export const twoSumTypeScript = `function twoSum(values: number[], target: number): number[] {
  const seen = new Map<number, number>();
  for (let index = 0; index < values.length; index += 1) {
    const value = values[index]!;
    const match = seen.get(target - value);
    if (match !== undefined) return [match, index];
    seen.set(value, index);
  }
  return [];
}`;
