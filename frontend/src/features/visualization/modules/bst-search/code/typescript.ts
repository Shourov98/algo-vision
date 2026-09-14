export const bstSearchTypeScript = `function search(root: Node | null, target: number): Node | null {
  let current = root;
  while (current !== null) {
    if (target === current.value) return current;
    current = target < current.value ? current.left : current.right;
  }
  return null;
}`;
