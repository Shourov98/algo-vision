export const bstInsertCpp = `Node* insert(Node* root, int value) {
  if (root == nullptr) return new Node{value, nullptr, nullptr};
  Node* current = root;
  while (true) {
    if (value == current->value) return root;
    Node*& child = value < current->value ? current->left : current->right;
    if (child == nullptr) {
      child = new Node{value, nullptr, nullptr};
      return root;
    }
    current = child;
  }
}`;
