"""Deterministic report generator.

This is a normal rule-based Python function, not an LLM.
"""

from __future__ import annotations


def generate_report(context: dict) -> str:
    avg = float(context["historical_average_temperature_c"])
    current = float(context["current_singapore_temperature_c"])
    diff = current - avg

    if avg >= 28.0 or current >= 30.0:
        advice = "Turn on the aircon if comfort is required."
    else:
        advice = "Aircon may not be necessary; consider fan or natural ventilation."

    return (
        "Temperature Comfort Report\n\n"
        f"Historical average indoor temperature: {avg:.1f} C\n"
        f"Current Singapore temperature: {current:.1f} C\n"
        f"Difference: {diff:.1f} C\n"
        f"Recommendation: {advice}"
    )
