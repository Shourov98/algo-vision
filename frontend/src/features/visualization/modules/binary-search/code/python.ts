export const binarySearchPython = `def binary_search(values: list[int], target: int) -> int:
    low, high = 0, len(values) - 1
    while low <= high:
        middle = low + (high - low) // 2
        candidate = values[middle]
        if candidate == target:
            return middle
        if candidate < target:
            low = middle + 1
        else:
            high = middle - 1
    return -1`;
