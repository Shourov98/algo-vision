export const bstSearchPython = `def search(root: Node | None, target: int) -> Node | None:
    current = root
    while current is not None:
        if target == current.value:
            return current
        current = current.left if target < current.value else current.right
    return None`;
