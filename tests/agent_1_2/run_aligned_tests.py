"""
Clean, aligned test runner for Agent 1 & Agent 2 test suites.
Discovers all tests in tests/agent_1_2, executes them, and prints
a structured, categorized summary table with pass/fail metrics.
Pure Python standard library (zero external dependencies).
"""
from __future__ import annotations

import io
import os
import sys
import time
import unittest

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())


def _categorize_test(test_id: str) -> str:
    """Group tests logically into cohesive audit categories."""
    if "test_16_scenario_benchmark" in test_id:
        return "16-Scenario Benchmark (Rule 19.1 & 19.2)"
    elif "test_contract_shape_and_blocking" in test_id:
        return "Contract Shape & Invariant Guards (v1.1)"
    elif "test_conversational_e2e" in test_id:
        return "Multi-Turn Conversational E2E (Root-Cause Flow)"
    elif "test_agent_1_unittest" in test_id:
        return "Agent 1 Unitary Intake & Distress Parsing"
    elif "test_agent_2_unittest" in test_id:
        return "Agent 2 4-Gate Filter & Pacing Ceiling"
    elif "test_comprehensive_regression" in test_id:
        return "Regression Probes & Isolation Defenses"
    elif "test_pr_fixes_unittest" in test_id:
        return "PR Merge Blockers & Character Normalization"
    elif "test_architectural_audit" in test_id:
        return "Self-Contained Architectural Audit"
    return "Other Component Checks"


def run_aligned_suite():
    loader = unittest.TestLoader()
    suite_dir = os.path.join(REPO_ROOT, "tests", "agent_1_2")
    suite = loader.discover(start_dir=suite_dir, top_level_dir=REPO_ROOT)

    # Flatten suite into list of test cases
    test_cases = []
    def _collect(s):
        for item in s:
            if isinstance(item, unittest.TestSuite):
                _collect(item)
            else:
                test_cases.append(item)
    _collect(suite)

    # Group test cases by category
    categorized = {}
    for test in test_cases:
        cat = _categorize_test(test.id())
        categorized.setdefault(cat, []).append(test)

    print("=" * 96)
    print(" AI COMMUNITY AID NAVIGATOR — AGENT 1 & AGENT 2 TEST SUITE")
    print(" Contracts: Shared JSON Contracts v1.1 | Python: 3.11+ Standard Library")
    print("=" * 96)

    total_run = 0
    total_passed = 0
    total_failed = 0
    total_errors = 0
    start_time = time.time()

    col_w_idx = 4
    col_w_name = 62
    col_w_time = 12
    col_w_status = 10

    for cat_name, tests_in_cat in sorted(categorized.items()):
        print(f"\n[Category] {cat_name}")
        print("-" * 96)
        print(f" {'#':<{col_w_idx}} | {'Test Method Name':<{col_w_name}} | {'Time (s)':<{col_w_time}} | {'Status':<{col_w_status}}")
        print("-" * 96)

        for idx, test in enumerate(tests_in_cat, start=1):
            total_run += 1
            test_name = test._testMethodName
            
            # Run test with suppressed stdout
            t_start = time.perf_counter()
            single_suite = unittest.TestSuite([test])
            devnull = io.StringIO()
            runner = unittest.TextTestRunner(stream=devnull, verbosity=0)
            res = runner.run(single_suite)
            t_elapsed = time.perf_counter() - t_start

            if res.wasSuccessful():
                total_passed += 1
                status = "PASS"
            elif res.failures:
                total_failed += 1
                status = "FAIL"
            else:
                total_errors += 1
                status = "ERROR"

            # Truncate method name cleanly if overly long
            display_name = (test_name[:col_w_name - 3] + "...") if len(test_name) > col_w_name else test_name
            print(f" {idx:<{col_w_idx}} | {display_name:<{col_w_name}} | {t_elapsed:<{col_w_time}.4f} | {status:<{col_w_status}}")

    total_duration = time.time() - start_time

    print("\n" + "=" * 96)
    print(f" SUMMARY METRICS")
    print("=" * 96)
    print(f"  • Total Tests Executed : {total_run}")
    print(f"  • Passed               : {total_passed} ({total_passed/total_run*100:.1f}%)")
    print(f"  • Failed               : {total_failed}")
    print(f"  • Errors               : {total_errors}")
    print(f"  • Total Execution Time : {total_duration:.3f}s")
    print(f"  • Overall Status       : {'ALL TESTS PASSED [OK]' if total_failed == 0 and total_errors == 0 else 'TESTS FAILED'}")
    print("=" * 96 + "\n")

    return 0 if (total_failed == 0 and total_errors == 0) else 1


if __name__ == "__main__":
    sys.exit(run_aligned_suite())