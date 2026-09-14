export const bstInsertTypeScript = `function insert(root: Node | null, value: number): Node {
  if (root === null) return { value, left: null, right: null };

  let current = root;
  while (true) {
    if (value === current.value) return root;
    const side = value < current.value ? "left" : "right";
    if (current[side] === null) {
      current[side] = { value, left: null, right: null };
      return root;
    }
    current = current[side]!;
  }
}`;
