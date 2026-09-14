export const binarySearchCpp = `int binarySearch(const std::vector<int>& values, int target) {
  int low = 0;
  int high = static_cast<int>(values.size()) - 1;
  while (low <= high) {
    const int middle = low + (high - low) / 2;
    const int candidate = values[middle];
    if (candidate == target) return middle;
    if (candidate < target) low = middle + 1;
    else high = middle - 1;
  }
  return -1;
}`;
