export const bubbleSortPython = `def bubble_sort(values: list[int]) -> list[int]:
    items = values.copy()

    for pass_index in range(len(items) - 1):
        for index in range(len(items) - pass_index - 1):
            if items[index] > items[index + 1]:
                items[index], items[index + 1] = items[index + 1], items[index]

    return items`;
