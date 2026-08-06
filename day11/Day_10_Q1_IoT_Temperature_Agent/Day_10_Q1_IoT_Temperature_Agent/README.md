# Lab 1 — IoT Temperature Agent with MCP Tools

This folder contains the source files listed in Section 4.3 of the Day 10 MCP + Agent Applications lab handout.

The lab demonstrates:

- an MCP tool implemented directly inside an MCP server;
- an MCP tool that wraps an external C++ executable;
- a mock HTTP weather service;
- an agent controller loop;
- deterministic, simulated LLM, and optional real LLM report generation.

The required parts of the lab are Level 1–3. Level 4 is optional.

---

## 1. Python version requirement

This lab requires **Python 3.10 or later**.

Check your Python version before creating the virtual environment:

```bash
python3 --version
which python3
```

On macOS, the system Python may be Python 3.9, which is too old for the `mcp[cli]` package. If your `python3` is Python 3.9, install a newer Python first.

For example, Python installed from `python.org` may be available at:

```bash
/Library/Frameworks/Python.framework/Versions/3.14/bin/python3
```

Use that full path when creating `.venv` if necessary.

---

## 2. Create and activate `.venv`

### macOS / Linux

If `python3` is already Python 3.10 or later:

```bash
python3 -m venv .venv
source .venv/bin/activate
python --version
```

If your default `python3` is still old, use the full path to the newer Python:

```bash
/Library/Frameworks/Python.framework/Versions/3.14/bin/python3 -m venv .venv
source .venv/bin/activate
python --version
```

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\.venv\Scripts\Activate.ps1
```

---

## 3. Install dependencies

With `.venv` activated:

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

The `requirements.txt` file contains:

```text
mcp[cli]
requests
```

Verify:

```bash
python -c "import mcp; import requests; print('OK')"
```

Expected output:

```text
OK
```

---

## 4. Run the mock weather server

Open **Terminal A** and keep it running.

Activate `.venv` first:

```bash
source .venv/bin/activate
```

Then run:

```bash
python weather_server/mock_weather_server.py
```

Check in browser:

```text
http://localhost:60004/current_temperature
```

Or check from terminal:

```bash
curl http://localhost:60004/current_temperature
```

Expected output is similar to:

```json
{
  "location": "Singapore",
  "temperature_c": 31.0,
  "condition": "Cloudy",
  "source": "mock classroom HTTP server"
}
```

If you open only:

```text
http://localhost:60004/
```

you may see:

```json
{
  "error": true,
  "message": "Unknown endpoint"
}
```

This is normal. Use the full endpoint path:

```text
/current_temperature
```

### Optional instructor-hosted mode

The instructor may run:

```bash
python weather_server/mock_weather_server.py --host 0.0.0.0 --port 60004
```

Students then set `weather_url` in `config.json` to:

```text
http://<instructor-ip>:60004/current_temperature
```

This works only if instructor and students are on the same LAN/WiFi and the network allows peer-to-peer access.

---

## 5. Open a second terminal for the agent controller

Because Terminal A is running the mock weather server, open **Terminal B** for the agent controller.

Activate `.venv` again in Terminal B:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Each new terminal session needs its own `.venv` activation.

---

## 6. Run Level 1 — internal MCP average tool

```bash
python agent/agent_controller.py --calculator internal --report deterministic
```

Expected flow:

```text
read_temperature_file
calculate_average_internal
mock weather HTTP service
deterministic report
```

---

## 7. Compile the external C++ calculator

### Windows PowerShell

```powershell
g++ cpp\average_calculator.cpp -o tools\average_calculator.exe
.\tools\average_calculator.exe numbers.txt
```

### macOS / Linux

```bash
mkdir -p tools
g++ cpp/average_calculator.cpp -o tools/average_calculator
./tools/average_calculator numbers.txt
```

Expected output:

```json
{
  "count": 5,
  "sum": 137.00,
  "average": 27.40
}
```

If macOS reports a permission error:

```bash
chmod +x tools/average_calculator
```

If the executable already runs, `chmod +x` is not needed.

---

## 8. Configure external executable path

For Windows, `config.json` should contain:

```json
"average_calculator_exe": "tools/average_calculator.exe"
```

For macOS/Linux, change it to:

```json
"average_calculator_exe": "tools/average_calculator"
```

---

## 9. Run Level 2 — external C++ calculator through MCP

```bash
python agent/agent_controller.py --calculator external --report deterministic
```

Expected flow:

```text
read_temperature_file
calculate_average_external
external C++ executable
mock weather HTTP service
deterministic report
```

---

## 10. Run Level 3 — simulated LLM report

```bash
python agent/agent_controller.py --calculator external --report simulated-llm
```

This does not call a paid LLM API. It uses a local Python function with an LLM-compatible input/output interface.

---

## 11. Optional Level 4 — real LLM through Claude Code CLI

Level 4 is optional.

In this version, `real-llm` mode calls **Claude Code CLI** from Python using `subprocess`.

This mode does **not** require an Anthropic API key, but it does require Claude Code CLI to be installed and authenticated.

Verify Claude Code CLI first:

```bash
which claude
claude --version
claude -p "Write one short sentence saying this is a Claude Code CLI test."
```

Then run:

```bash
python agent/agent_controller.py --calculator external --report real-llm
```

Expected evidence includes lines similar to:

```text
[Real LLM] Calling Claude Code CLI at: /Users/.../.local/bin/claude
[Real LLM] Sending structured temperature context to Claude Code
```

If Claude Code CLI is unavailable, use Level 3:

```bash
python agent/agent_controller.py --calculator external --report simulated-llm
```

---

## 12. Loop mode

```bash
python agent/agent_controller.py --calculator external --report simulated-llm --loop --interval 20 --timeout 120
```

While it is running, edit `numbers.txt`; the next iteration should generate a changed report.

Exit conditions:

- press `q` then Enter during the waiting period;
- timeout;
- maximum iterations;
- unrecoverable tool or service error;
- Ctrl+C.
