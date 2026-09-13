export const bstInsertPython = `def insert(root: Node | None, value: int) -> Node:
    if root is None:
        return Node(value)
    current = root
    while True:
        if value == current.value:
            return root
        side = "left" if value < current.value else "right"
        if getattr(current, side) is None:
            setattr(current, side, Node(value))
            return root
        current = getattr(current, side)`;
