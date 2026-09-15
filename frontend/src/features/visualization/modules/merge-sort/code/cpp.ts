export const mergeSortCpp = `vector<int> mergeSort(vector<int> values) {
  if (values.size() <= 1) return values;

  int middle = values.size() / 2;
  vector<int> left(values.begin(), values.begin() + middle);
  vector<int> right(values.begin() + middle, values.end());
  return merge(mergeSort(left), mergeSort(right));
}`;
