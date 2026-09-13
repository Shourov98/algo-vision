export const quickSortCpp = `std::vector<int> quickSort(const std::vector<int>& values) {
  if (values.size() <= 1) return values;
  const int pivot = values.back();
  std::vector<int> smaller, larger;
  for (std::size_t index = 0; index + 1 < values.size(); ++index) {
    (values[index] <= pivot ? smaller : larger).push_back(values[index]);
  }
  smaller = quickSort(smaller);
  larger = quickSort(larger);
  smaller.push_back(pivot);
  smaller.insert(smaller.end(), larger.begin(), larger.end());
  return smaller;
}`;
