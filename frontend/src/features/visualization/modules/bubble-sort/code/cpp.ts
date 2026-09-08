export const bubbleSortCpp = `#include <vector>
#include <utility>

std::vector<int> bubbleSort(std::vector<int> values) {
  for (std::size_t pass = 0; pass + 1 < values.size(); ++pass) {
    for (std::size_t index = 0; index + pass + 1 < values.size(); ++index) {
      if (values[index] > values[index + 1]) {
        std::swap(values[index], values[index + 1]);
      }
    }
  }

  return values;
}`;
