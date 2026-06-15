

import os
import sys

from eval.scenarios import SCENARIOS


def _collect_tool_calls(messages) -> list[dict]:
    """Extract tool calls from an agent result's message list."""
    calls = []
    for m in messages:
        for tc in getattr(m, "tool_calls", None) or []:
            # tool_calls entries look like {"name": ..., "args": {...}, "id": ...}
            calls.append({"name": tc.get("name"), "args": tc.get("args", {})})
    return calls


def run():
    if not os.getenv("GROQ_API_KEY"):
        print("GROQ_API_KEY not set — cannot run the live eval.")
        sys.exit(1)

    from shopping_agent import agent  

    total_checks = 0
    passed_checks = 0
    failed_scenarios = []

    for scenario in SCENARIOS:
        history: list[dict] = []
        all_tool_calls: list[dict] = []
        final_text = ""

        for turn in scenario.turns:
            history.append({"role": "user", "content": turn})
            result = agent.invoke({"messages": history})
            all_tool_calls.extend(_collect_tool_calls(result["messages"]))
            final_text = result["messages"][-1].content
            history.append({"role": "assistant", "content": final_text})

        print(f"\n=== {scenario.name} ===")
        scenario_ok = True
        for check in scenario.checks:
            ok, detail = check(all_tool_calls, final_text)
            total_checks += 1
            passed_checks += int(ok)
            print(f"  [{'PASS' if ok else 'FAIL'}] {detail}")
            scenario_ok = scenario_ok and ok
        if not scenario_ok:
            failed_scenarios.append(scenario.name)

    print(f"\n{passed_checks}/{total_checks} checks passed.")
    if failed_scenarios:
        print("Failed scenarios:", ", ".join(failed_scenarios))
        sys.exit(1)


if __name__ == "__main__":
    run()
