export const twoSumCpp = `std::vector<int> twoSum(const std::vector<int>& values, int target) {
  std::unordered_map<int, int> seen;
  for (int index = 0; index < static_cast<int>(values.size()); ++index) {
    const int value = values[index];
    if (auto match = seen.find(target - value); match != seen.end()) return {match->second, index};
    seen[value] = index;
  }
  return {};
}`;
