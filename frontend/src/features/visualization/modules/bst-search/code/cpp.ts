export const bstSearchCpp = `Node* search(Node* root, int target) {
  Node* current = root;
  while (current != nullptr) {
    if (target == current->value) return current;
    current = target < current->value ? current->left : current->right;
  }
  return nullptr;
}`;
