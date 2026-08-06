#include <cctype>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

static std::string trim(const std::string &s) {
  size_t start = 0;
  while (start < s.size() && std::isspace(static_cast<unsigned char>(s[start]))) {
    ++start;
  }
  size_t end = s.size();
  while (end > start && std::isspace(static_cast<unsigned char>(s[end - 1]))) {
    --end;
  }
  return s.substr(start, end - start);
}

int main(int argc, char *argv[]) {
  if (argc != 2) {
    std::cerr << "Usage: average_calculator <numbers.txt>\n";
    return 1;
  }

  std::ifstream fin(argv[1]);
  if (!fin) {
    std::cerr << "Error: cannot open input file: " << argv[1] << "\n";
    return 2;
  }

  std::vector<double> values;
  std::string line;
  int line_no = 0;

  while (std::getline(fin, line)) {
    ++line_no;
    std::string t = trim(line);
    if (t.empty() || t[0] == '#') {
      continue;
    }

    char *endptr = nullptr;
    double value = std::strtod(t.c_str(), &endptr);
    if (endptr == t.c_str()) {
      std::cerr << "Error: invalid number at line " << line_no << ": " << line << "\n";
      return 3;
    }
    values.push_back(value);
  }

  if (values.empty()) {
    std::cerr << "Error: no valid numeric values found.\n";
    return 4;
  }

  double sum = 0.0;
  for (double v : values) {
    sum += v;
  }
  double average = sum / static_cast<double>(values.size());

  std::cout << std::fixed << std::setprecision(2);
  std::cout << "{\n";
  std::cout << "  \"count\": " << values.size() << ",\n";
  std::cout << "  \"sum\": " << sum << ",\n";
  std::cout << "  \"average\": " << average << "\n";
  std::cout << "}\n";

  return 0;
}
