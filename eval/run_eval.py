"""
Behavioural eval runner for the shopping agent.

Drives real agent conversations, checks properties, and logs
pass rates to eval/results.json for tracking across runs.

Usage:
    python -m eval.run_eval              # run all scenarios
    python -m eval.run_eval --scenario browse_does_not_order
"""

import argparse
import json
import os
import sys
from datetime import datetime

from eval.scenarios import SCENARIOS


def _collect_tool_calls(messages) -> list[dict]:
    calls = []
    for m in messages:
        for tc in getattr(m, "tool_calls", None) or []:
            calls.append({"name": tc.get("name"), "args": tc.get("args", {})})
    return calls


def run(filter_name: str | None = None):
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set — cannot run live eval.")
        sys.exit(1)

    from shopping_agent import agent

    scenarios = SCENARIOS
    if filter_name:
        scenarios = [s for s in SCENARIOS if s.name == filter_name]
        if not scenarios:
            print(f"No scenario named '{filter_name}'")
            sys.exit(1)

    total_checks = 0
    passed_checks = 0
    failed_scenarios = []
    results = []

    for scenario in scenarios:
        history: list[dict] = []
        all_tool_calls: list[dict] = []
        final_text = ""

        for turn in scenario.turns:
            history.append({"role": "user", "content": turn})
            result = agent.invoke({"messages": history})
            all_tool_calls.extend(_collect_tool_calls(result["messages"]))
            final_text = result["messages"][-1].content
            history.append({"role": "assistant", "content": final_text})

        print(f"\n{'='*60}")
        print(f"SCENARIO: {scenario.name}")
        if scenario.description:
            print(f"  {scenario.description}")
        print(f"{'='*60}")

        scenario_checks = []
        scenario_ok = True
        for check in scenario.checks:
            ok, detail = check(all_tool_calls, final_text)
            total_checks += 1
            passed_checks += int(ok)
            status = "PASS ✓" if ok else "FAIL ✗"
            print(f"  [{status}] {detail}")
            scenario_checks.append({"detail": detail, "passed": ok})
            scenario_ok = scenario_ok and ok

        if not scenario_ok:
            failed_scenarios.append(scenario.name)

        results.append({
            "scenario": scenario.name,
            "passed": scenario_ok,
            "checks": scenario_checks,
        })

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"RESULTS: {passed_checks}/{total_checks} checks passed "
          f"({len(scenarios) - len(failed_scenarios)}/{len(scenarios)} scenarios)")
    if failed_scenarios:
        print(f"Failed: {', '.join(failed_scenarios)}")
    print(f"{'='*60}")

    # ── Save to results.json for pass-rate tracking ───────────────────────────
    results_path = os.path.join(os.path.dirname(__file__), "results.json")
    history_entry = {
        "timestamp": datetime.now().isoformat(),
        "model": os.getenv("TEXT_MODEL", "gpt-4o"),
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "pass_rate": round(passed_checks / total_checks * 100, 1),
        "scenarios": results,
    }

    existing = []
    if os.path.exists(results_path):
        try:
            existing = json.loads(open(results_path).read())
        except Exception:
            existing = []

    existing.append(history_entry)
    with open(results_path, "w") as f:
        json.dump(existing, f, indent=2)

    print(f"\nResults saved to eval/results.json")
    print(f"Pass rate: {history_entry['pass_rate']}%")

    if failed_scenarios:
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", help="Run a single scenario by name")
    args = parser.parse_args()
    run(filter_name=args.scenario)
