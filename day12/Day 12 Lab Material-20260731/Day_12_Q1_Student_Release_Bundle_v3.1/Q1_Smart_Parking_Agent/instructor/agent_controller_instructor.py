from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from controller.controller_helpers import save_candidate, source_hash, write_final_state, write_trace
from mcp_tools.mcp_client import call_tool
from revisers import claude_reviser, simulated_reviser


def choose_next_action(state: dict, compile_result: dict,
                       test_result: dict | None) -> tuple[str, str]:
    """Instructor implementation inserted after the student decision TODOs."""
    # TODO: compilation failure should normally request REPAIR.
    if not compile_result["success"]:
        return "REPAIR", "compilation_failed"
    # TODO: all tests passing should ACCEPT.
    if test_result and test_result["success"]:
        return "ACCEPT", "all_tests_passed"
    # TODO: enforce the iteration budget.
    if state["iteration"] >= state["max_iterations"]:
        return "STOP", "iteration_budget_exhausted"
    # TODO: escalate a repeated failure signature.
    signature = test_result["failure_signature"] if test_result else "compile_failure"
    if signature in state["failure_signatures"]:
        return "ESCALATE", "repeated_failure_signature"
    return "REPAIR", "tests_failed"


async def run_loop(mode: str, test_file: str, max_iterations: int) -> dict:
    source_path = ROOT / "workspace" / "settlement_engine.cpp"
    state = {"status": "RUNNING", "iteration": 0, "repairs": 0,
             "max_iterations": max_iterations, "failure_signatures": [],
             "candidate_hashes": []}
    save_candidate(source_path.read_text(encoding="utf-8"), 0)

    # TODO: implement the bounded observe-decide-act loop.
    # Instructor implementation inserted at the corresponding TODO.
    while True:
        source = source_path.read_text(encoding="utf-8")
        digest = source_hash(source)
        if digest in state["candidate_hashes"]:
            state.update(status="ESCALATED", stop_reason="repeated_candidate_hash")
            break
        state["candidate_hashes"].append(digest)

        compile_result = await call_tool(
            "compile_cpp", {"source_path": "workspace/settlement_engine.cpp"})
        test_result = None
        if compile_result["success"]:
            test_result = await call_tool("run_tests", {"test_file": test_file})

        action, reason = choose_next_action(state, compile_result, test_result)
        print(f"Iteration {state['iteration']}: "
              f"compile={'PASS' if compile_result['success'] else 'FAIL'}", end="")
        if test_result:
            print(f", tests={test_result['passed']}/{test_result['total']}", end="")
        print(f", decision={action} ({reason})")
        write_trace({"iteration": state["iteration"], "candidate_hash": digest,
                     "compile": compile_result, "tests": test_result,
                     "decision": action, "reason": reason})

        if action == "ACCEPT":
            state.update(status="PASSED", stop_reason=reason, test_result=test_result)
            break
        if action in {"STOP", "ESCALATE"}:
            status = "ESCALATED" if action == "ESCALATE" else "STOPPED"
            state.update(status=status, stop_reason=reason, test_result=test_result)
            break

        if test_result:
            state["failure_signatures"].append(test_result["failure_signature"])
        evidence = {"compile": compile_result, "tests": test_result}
        reviser = simulated_reviser if mode == "simulated" else claude_reviser
        revised = reviser.revise(source, evidence, state["repairs"])
        state["repairs"] += 1
        state["iteration"] += 1
        save_candidate(revised, state["iteration"])

    write_final_state(state)
    print(f"Final status: {state['status']} -- {state['stop_reason']}")
    return state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviser", choices=["simulated", "claude"], default="simulated")
    parser.add_argument("--tests", default="tests/example_tests.json")
    parser.add_argument("--max-iterations", type=int, default=4)
    args = parser.parse_args()
    asyncio.run(run_loop(args.reviser, args.tests, args.max_iterations))


if __name__ == "__main__":
    main()
