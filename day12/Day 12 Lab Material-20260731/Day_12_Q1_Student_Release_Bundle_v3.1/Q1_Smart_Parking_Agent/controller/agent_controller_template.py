from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))

from controller.controller_helpers import save_candidate, source_hash, write_final_state, write_trace
from mcp_tools.mcp_client import call_tool
from revisers import claude_reviser, simulated_reviser


def choose_next_action(state: dict, compile_result: dict, test_result: dict | None) -> tuple[str, str]:
    """TODO: return (action, reason). Actions: ACCEPT, REPAIR, STOP, ESCALATE."""
    failure_signature = None

    if test_result:
        failure_signature = test_result.get("failure_signature")

    if not failure_signature:
        failure_signature = compile_result.get("failure_signature")

    # TODO: compilation failure should normally request REPAIR.
    if compile_result.get("status") != "PASS":
        if state["iteration"] >= state["max_iterations"]:
            return "STOP", "max_iterations_reached"

        if (
            failure_signature
            and failure_signature in state["failure_signatures"]
        ):
            return "ESCALATE", "repeated_failure_signature"

        return "REPAIR", "compile_failed"
    # TODO: all tests passing should ACCEPT.
    if test_result and test_result.get("status") == "PASS":
        return "ACCEPT", "all_tests_passed"
    
    # TODO: enforce the iteration budget.
    if state["iteration"] >= state["max_iterations"]:
        return "STOP", "max_iterations_reached"

    # TODO: escalate a repeated failure signature.
    if (
        failure_signature
        and failure_signature in state["failure_signatures"]
    ):
        return "ESCALATE", "repeated_failure_signature"

    # Compilation passed, but one or more tests failed.
    if test_result and test_result.get("status") == "FAIL":
        return "REPAIR", "tests_failed"

    return "ESCALATE", "unexpected_tool_result"


async def run_loop(mode: str, test_file: str, max_iterations: int) -> dict:
    source_path = ROOT / "workspace" / "settlement_engine.cpp"
    state = {"status": "RUNNING", "iteration": 0, "repairs": 0,
             "max_iterations": max_iterations, "failure_signatures": [], "candidate_hashes": []}
    save_candidate(source_path.read_text(encoding="utf-8"), 0)

    # TODO: implement the bounded observe-decide-act loop using:
    #   await call_tool("compile_cpp", {...})
    #   await call_tool("run_tests", {...})
    #   choose_next_action(...)
    #   simulated_reviser.revise(...) or claude_reviser.revise(...)
    #   save_candidate(...), write_trace(...), write_final_state(...)
    # Stop on ACCEPT, STOP, ESCALATE, or a repeated candidate hash.
    import inspect

    while True:
        current_source = source_path.read_text(
            encoding="utf-8"
        )
        current_hash = source_hash(current_source)

        if current_hash in state["candidate_hashes"]:
            state["status"] = "ESCALATED"
            state["reason"] = "repeated_candidate_hash"

            write_trace({
                "iteration": state["iteration"],
                "candidate_hash": current_hash,
                "action": "ESCALATE",
                "reason": state["reason"]
            })

            write_final_state(state)
            return state

        state["candidate_hashes"].append(current_hash)

        source_arg = "workspace/settlement_engine.cpp"
        test_arg = Path(test_file).as_posix().removeprefix("./")

        compile_result = await call_tool(
            "compile_cpp",
            {"source_path": source_arg}
        )

        test_result = None

        if compile_result.get("status") == "PASS":
            test_result = await call_tool(
                "run_tests",
                {"test_file": test_arg}
            )

        action, reason = choose_next_action(
            state,
            compile_result,
            test_result
        )

        failure_signature = (
            test_result.get("failure_signature")
            if test_result
            else compile_result.get("failure_signature")
        )

        write_trace({
            "iteration": state["iteration"],
            "candidate_hash": current_hash,
            "compile_result": compile_result,
            "test_result": test_result,
            "action": action,
            "reason": reason
        })

        print(
            f"Iteration {state['iteration']}: "
            f"compile={compile_result.get('status')}, "
            f"tests={test_result.get('status') if test_result else 'SKIPPED'}, "
            f"decision={action}"
        )

        # Save signature after deciding so the first failure
        # repairs and the second identical failure escalates.
        if (
            failure_signature
            and failure_signature
            not in state["failure_signatures"]
        ):
            state["failure_signatures"].append(
                failure_signature
            )

        if action in {"ACCEPT", "STOP", "ESCALATE"}:
            status_map = {
                "ACCEPT": "PASSED",
                "STOP": "STOPPED",
                "ESCALATE": "ESCALATED"
            }

            state["status"] = status_map[action]
            state["reason"] = reason
            state["final_action"] = action

            write_final_state(state)

            print(
                f"Final status: {state['status']} -- "
                f"{reason}"
            )

            return state

        # Select simulated or Claude reviser.
        reviser = (
            simulated_reviser
            if mode == "simulated"
            else claude_reviser
        )

        rules_path = (
            ROOT / "specs" / "settlement_rules.txt"
        )

        rules = (
            rules_path.read_text(encoding="utf-8")
            if rules_path.exists()
            else ""
        )

        # Supply values according to the reviser's
        # actual parameter names.
        possible_values = {
            "source": current_source,
            "current_source": current_source,
            "compile_result": compile_result,
            "test_result": test_result,
            "evidence": {
                "compile_result": compile_result,
                "test_result": test_result
            },
            "state": state,
            "iteration": state["iteration"],
            "repair_number": state["repairs"] + 1,
            "repair_index": state["repairs"] + 1,
            "candidate_index": state["iteration"] + 1,
            "rules": rules,
            "specification": rules,
            "test_file": test_file
        }

        parameters = inspect.signature(
            reviser.revise
        ).parameters

        arguments = {
            name: possible_values[name]
            for name in parameters
            if name in possible_values
        }

        revised_source = reviser.revise(**arguments)

        if inspect.isawaitable(revised_source):
            revised_source = await revised_source

        if isinstance(revised_source, dict):
            revised_source = (
                revised_source.get("source")
                or revised_source.get("revised_source")
            )

        if not isinstance(revised_source, str):
            raise RuntimeError(
                "Reviser did not return C++ source"
            )

        state["repairs"] += 1
        state["iteration"] += 1

        save_candidate(
            revised_source,
            state["iteration"]
        )
        
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviser", choices=["simulated", "claude"], default="simulated")
    parser.add_argument("--tests", default="tests/example_tests.json")
    parser.add_argument("--max-iterations", type=int, default=4)
    args = parser.parse_args()
    asyncio.run(run_loop(args.reviser, args.tests, args.max_iterations))


if __name__ == "__main__":
    main()
