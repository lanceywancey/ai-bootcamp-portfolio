# Troubleshooting — Lab 1 IoT Temperature Agent

## `g++` is not recognized

Install a C++ compiler such as MinGW/MSYS2 on Windows, Xcode command line tools on macOS, or build-essential on Ubuntu.

## External calculator executable not found

Compile the C++ program and place it in `tools/`.

Windows:

```powershell
g++ cpp\average_calculator.cpp -o tools\average_calculator.exe
```

macOS/Linux:

```bash
g++ cpp/average_calculator.cpp -o tools/average_calculator
```

Then check `average_calculator_exe` in `config.json`.

## Weather server connection refused

Make sure the mock weather server is running:

```bash
python weather_server/mock_weather_server.py
```

Open this URL in a browser:

```text
http://localhost:60004/current_temperature
```

For instructor-hosted mode, check WiFi client isolation and Windows/macOS firewall settings.

## MCP server fails because JSON-RPC output is corrupted

For stdio-based MCP servers, normal debug logs should go to `stderr`, not `stdout`. The provided server prints its startup log to `stderr`.

## `ModuleNotFoundError: No module named mcp`

Install Python dependencies in the active virtual environment:

```bash
pip install -r requirements.txt
```

## The simulated LLM report is not a real LLM

That is expected. Level 3 is designed to show the software interface without requiring paid API access. Level 4 is optional.
