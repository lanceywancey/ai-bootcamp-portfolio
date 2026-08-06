# Day 12 Q1 — Smart Parking Agentic Repair Lab

This bundle supports the required Day 12 exercise: build and test a C++17 settlement engine, then control a bounded compile–test–repair loop from Python through two supplied MCP tools.

The scenario combines parking fees with EV charging and vehicle-to-grid (V2G) export. A negative net amount is valid and means the system owes the driver a credit.

## What students complete

Students own three files:

1. `workspace/settlement_engine.cpp` — complete the four C++ TODOs.
2. `tests/student_tests.json` — add meaningful policy, boundary, invalid-input, rounding, and settlement tests.
3. `controller/agent_controller_template.py` — complete the decision function and bounded loop.

The remaining files are supplied infrastructure or reference material. Do not modify the MCP server, deterministic reviser, or web interface during the guided exercise.

## Directory guide

```text
Q1_Smart_Parking_Agent/
├── README.md                         this guide
├── requirements.txt                  Python dependencies
├── config/
│   └── app_config.json               Flask host and port
├── specs/
│   └── settlement_rules.txt          authoritative simplified policy
├── workspace/
│   └── settlement_engine.cpp         student C++ starter/current candidate
├── tests/
│   ├── example_tests.json            five visible guided cases
│   └── student_tests.json            student-owned test file
├── controller/
│   ├── agent_controller_template.py  student controller TODOs
│   └── controller_helpers.py         candidate, hash, trace, state helpers
├── mcp_tools/
│   ├── mcp_server.py                 supplied typed compile/test tools
│   └── mcp_client.py                 local stdio MCP client wrapper
├── revisers/
│   ├── simulated_reviser.py          deterministic required reviser
│   ├── claude_reviser.py             optional Claude Code CLI adapter
│   └── simulated_candidates/         prepared teaching candidates
├── instructor/
│   ├── agent_controller_instructor.py      released reference controller
│   ├── settlement_engine_instructor.cpp    instructor-only reference C++
│   └── student_tests_instructor.json       instructor-only fuller test suite
├── demo/
│   ├── app.py                        supplied Flask form and JSON API
│   ├── templates/                    web page
│   └── static/                       presentation style
├── instructor_tests/                 additional instructor acceptance tests
├── candidates/                       generated preserved C++ candidates
├── logs/                             generated JSONL audit trace
└── state/                            generated final loop state
```

Empty `__init__.py` files mark Python package directories. Keep them: they make imports and tooling more predictable across Python versions, IDEs, macOS, and Windows.

## Student release versus instructor master

Maintain one instructor master bundle and derive the student release from it.

The student release **includes**:

- `instructor/agent_controller_instructor.py`, because it is a diagnostic and comparison aid;
- the incomplete student C++ source, student test template, and student controller template;
- the supplied MCP, reviser, and web infrastructure.

Before releasing to students, remove these instructor-only items:

- `instructor/settlement_engine_instructor.cpp`;
- `instructor/student_tests_instructor.json`;
- `instructor_tests/` if the additional acceptance tests should remain hidden.

The complete controller does not replace the student task. Students must complete their own template and explain its state transitions, repeat detection, evidence, and stopping conditions.

## Simplified settlement assumptions

- `ICE_CAR` means Internal Combustion Engine car.
- One settlement record covers 0–1440 minutes inclusive. This one-day limit simplifies Q1; a production system would split or aggregate multi-day stays according to its policy.
- Up to 15 minutes is free. Later fees use started hours and daily caps.
- Energy values use Wh; tariffs use cents/kWh; monetary results use integer cents.
- Export is allowed only for an EV when vehicle capability, station capability, owner opt-in, and minimum departure SOC conditions all hold.
- `net = parking + import − export`.
- Positive is `PAY`, zero is `ZERO`, and negative is `CREDIT`.

Read `specs/settlement_rules.txt` before implementing anything.

## The two supplied typed MCP capabilities

`compile_cpp(source_path)` compiles one source inside a permitted source directory and returns structured evidence including success, exit code, compiler, executable path, stdout, and stderr.

`run_tests(test_file)` runs one permitted JSON test file against the compiled executable and returns success, passed/failed/total counts, failure details, and a stable failure signature.

The narrow typed interface is intentional. The controller does not give the reviser a general shell tool.

## macOS setup

From Terminal, enter the bundle directory and run:

```bash
python3 --version
clang++ --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -c "import flask, mcp; print(flask.__name__, mcp.__name__)"
python -m compileall controller mcp_tools revisers demo instructor
```

Expected dependency-check output is approximately:

```text
flask mcp
```

The command avoids nested apostrophes. If a command copied from a PDF produces an “invalid character `’`” error, retype the quotation marks in Terminal or copy from this README. The typographic apostrophe `’` (U+2019) is not the ASCII apostrophe `'` (U+0027).

If `clang++` is missing, run `xcode-select --install`, complete the installer, and open a new Terminal.

## Windows PowerShell setup

The guided Windows path uses MinGW-w64 `g++`:

```powershell
py -3 --version
g++ --version
py -3 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -c "import flask, mcp; print(flask.__name__, mcp.__name__)"
python -m compileall controller mcp_tools revisers demo instructor
```

The execution-policy change applies only to the current PowerShell process. Install an MSYS2/MinGW-w64 UCRT64 toolchain and add its `bin` directory to `Path` if `g++` is not found.

## Check student JSON syntax

macOS:

```bash
python -m json.tool tests/student_tests.json
```

PowerShell:

```powershell
python -m json.tool .\tests\student_tests.json
```

Success prints the same JSON in a consistently indented form. This only checks JSON syntax; it does not run tests or verify expected values.

## Run the controller

The unfinished student template intentionally raises:

```text
NotImplementedError: Complete run_loop
```

That result is normal before students implement its TODOs.

After completing it, run on macOS:

```bash
python controller/agent_controller_template.py \
  --reviser simulated --tests tests/example_tests.json --max-iterations 4
```

PowerShell:

```powershell
python .\controller\agent_controller_template.py `
  --reviser simulated --tests tests/example_tests.json --max-iterations 4
```

The PowerShell backtick must be the final character on its line. The entire command may instead be placed on one line.

To isolate student-controller problems, run the released reference controller by replacing the script path with:

```text
instructor/agent_controller_instructor.py
```

With the starter and supplied deterministic candidates, observe approximately:

```text
Iteration 0: compile=PASS, tests=0/5, decision=REPAIR
Iteration 1: compile=PASS, tests=4/5, decision=REPAIR
Iteration 2: compile=PASS, tests=5/5, decision=ACCEPT
Final status: PASSED -- all_tests_passed
```

Observe why each repair occurs. Candidate 1 still fails the minimum-departure-SOC case; candidate 2 fixes it.

## Inspect evidence

macOS:

```bash
ls candidates
cat state/final_state.json
tail -n 3 logs/trace.jsonl
```

PowerShell:

```powershell
Get-ChildItem .\candidates
Get-Content .\state\final_state.json
Get-Content .\logs\trace.jsonl -Tail 3
```

Observe:

- candidate hashes identify source versions;
- failure signatures identify repeated test evidence;
- compilation must pass before tests run;
- the iteration budget and repeat checks bound the loop;
- accepting visible tests is evidence, not proof of correctness.

## Run the web simulator

First produce and compile a working candidate. Then run:

```bash
python demo/app.py
```

The app reads `config/app_config.json`:

```json
{
  "host": "127.0.0.1",
  "port": 5000
}
```

Open the address printed by Flask. If port 5000 is occupied, stop Flask, change the config value to an unused port such as 5050, restart, and open `http://127.0.0.1:5050`.

Demonstrate at least:

- a positive `PAY` settlement;
- a negative `CREDIT` settlement;
- a V2G rejection caused by permission or departure-SOC policy.

All readings and plates are simulated. Stop Flask with Ctrl+C.

## Optional Claude Code mode

If the `claude` command is installed and authenticated through an eligible account, replace `--reviser simulated` with `--reviser claude`. This may consume the signed-in account’s usage allowance. Keep the iteration, repeat, path, and evidence controls enabled.

## Instructor verification

These commands are for the instructor master bundle, not the released student bundle.

macOS:

```bash
cp instructor/settlement_engine_instructor.cpp workspace/settlement_engine.cpp
cp instructor/student_tests_instructor.json tests/student_tests.json
python instructor/agent_controller_instructor.py \
  --reviser simulated --tests tests/student_tests.json --max-iterations 4
```

PowerShell:

```powershell
Copy-Item .\instructor\settlement_engine_instructor.cpp .\workspace\settlement_engine.cpp
Copy-Item .\instructor\student_tests_instructor.json .\tests\student_tests.json
python .\instructor\agent_controller_instructor.py `
  --reviser simulated --tests tests/student_tests.json --max-iterations 4
```

Copy rather than rename so the master references remain intact. Before testing the deterministic teaching progression again, restore the incomplete student starter; otherwise the complete instructor engine will be accepted immediately.

## What students should be able to explain

- Why this is a feedback-controlled loop rather than only a fixed pipeline.
- Why compilation and tests are observations rather than decisions.
- When the controller chooses `ACCEPT`, `REPAIR`, `STOP`, or `ESCALATE`.
- Why candidate hashes and failure signatures detect different kinds of repetition.
- Why a negative fee can be valid in bidirectional EV settlement.
- Why hidden tests, human review, and deployment controls are still necessary.
