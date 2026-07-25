import subprocess
import sys

test_cases = [
    (3, 4, 12),
    (0, 0, 0),
    (-3, 4, -12),
    (-3, -4, 12),
]

all_passed = True

for a, b, expected in test_cases:
    result = subprocess.check_output(
        ["./multiply", str(a), str(b)],
        text=True
    ).strip()

    print(f"{a} * {b} = {result}")

    if result != str(expected):
        print("FAILED")
        all_passed = False

if all_passed:
    print("ALL TESTS PASSED")
    sys.exit(0)
else:
    print("TEST FAILURE")
    sys.exit(1)