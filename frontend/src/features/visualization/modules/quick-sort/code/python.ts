export const quickSortPython = `def quick_sort(values: list[int]) -> list[int]:
    if len(values) <= 1:
        return values
    pivot = values[-1]
    smaller = [value for value in values[:-1] if value <= pivot]
    larger = [value for value in values[:-1] if value > pivot]
    return quick_sort(smaller) + [pivot] + quick_sort(larger)`;
