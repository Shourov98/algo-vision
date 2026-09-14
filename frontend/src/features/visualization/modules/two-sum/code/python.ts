export const twoSumPython = `def two_sum(values: list[int], target: int) -> list[int]:
    seen: dict[int, int] = {}
    for index, value in enumerate(values):
        if target - value in seen:
            return [seen[target - value], index]
        seen[value] = index
    return []`;
