from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from flask import Flask, jsonify, render_template, request

ROOT = Path(__file__).resolve().parents[1]
app = Flask(__name__)

DEFAULT_VALUES = {
    "parking_minutes": 120,
    "vehicle_type": "EV_CAR",
    "import_wh": 5000,
    "import_rate_cents_per_kwh": 10,
    "export_wh": 20000,
    "export_rate_cents_per_kwh": 30,
    "vehicle_v2g": True,
    "station_v2g": True,
    "owner_opt_in": True,
    "soc_after_export": 60,
    "minimum_departure_soc": 40,
}


def load_app_config() -> dict:
    path = ROOT / "config" / "app_config.json"
    config = json.loads(path.read_text(encoding="utf-8"))
    host = str(config.get("host", "127.0.0.1"))
    port = int(config.get("port", 5000))
    if not 1 <= port <= 65535:
        raise ValueError("config port must be between 1 and 65535")
    return {"host": host, "port": port}


def engine_path() -> Path:
    suffix = ".exe" if os.name == "nt" else ""
    return ROOT / "workspace" / f"settlement_engine{suffix}"


def run_engine(data: dict) -> dict:
    names = ["parking_minutes", "vehicle_type", "import_wh", "import_rate_cents_per_kwh",
             "export_wh", "export_rate_cents_per_kwh", "vehicle_v2g", "station_v2g",
             "owner_opt_in", "soc_after_export", "minimum_departure_soc"]
    arguments = [str(int(data[n])) if isinstance(data[n], bool) else str(data[n]) for n in names]
    executable = engine_path()
    if not executable.exists():
        return {"status": "error", "error": "Engine not compiled. Run the controller first."}
    completed = subprocess.run([str(executable), *arguments], capture_output=True, text=True,
                               timeout=5, cwd=ROOT)
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"status": "error", "error": "Engine returned invalid JSON",
                "details": completed.stderr[-500:]}


def form_data() -> dict:
    integer_fields = ["parking_minutes", "import_wh", "import_rate_cents_per_kwh",
                      "export_wh", "export_rate_cents_per_kwh", "soc_after_export",
                      "minimum_departure_soc"]
    data = {name: int(request.form.get(name, "0")) for name in integer_fields}
    data["vehicle_type"] = request.form.get("vehicle_type", "EV_CAR")
    for name in ["vehicle_v2g", "station_v2g", "owner_opt_in"]:
        data[name] = request.form.get(name) == "on"
    return data


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        values = form_data()
        return render_template("index.html", result=run_engine(values), values=values)
    return render_template("index.html", result=None, values=DEFAULT_VALUES)


@app.post("/api/settlement")
def api_settlement():
    return jsonify(run_engine(request.get_json(force=True)))


if __name__ == "__main__":
    settings = load_app_config()
    print(f"Smart Parking Simulator: http://{settings['host']}:{settings['port']}")
    app.run(host=settings["host"], port=settings["port"], debug=False)
