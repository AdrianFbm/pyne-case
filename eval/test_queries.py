"""Lightweight evaluation: run natural-language questions through the agent and check results."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent import ask

TESTS = [
    {
        "question": "How many customers are there?",
        "check": lambda r: r.get("data") is not None and int(r["data"].iloc[0, 0]) == 200,
        "description": "Total customer count should be 200",
    },
    {
        "question": "What are the product categories?",
        "check": lambda r: r.get("data") is not None and "Jaffles" in r["data"].to_string(),
        "description": "Should include 'Jaffles' category",
    },
    {
        "question": "Top 5 products by revenue",
        "check": lambda r: (
            r.get("data") is not None
            and len(r["data"]) == 5
            and r.get("sql") is not None
            and "order_items" in r["sql"].lower()
        ),
        "description": "Should return exactly 5 rows and join with order_items",
    },
    {
        "question": "How many orders were placed per channel?",
        "check": lambda r: (
            r.get("data") is not None
            and "order_channel" in " ".join(r["data"].columns).lower()
        ),
        "description": "Should group by order_channel",
    },
    {
        "question": "What is the average order value?",
        "check": lambda r: (
            r.get("data") is not None
            and r["data"].iloc[0, 0] is not None
            and float(r["data"].iloc[0, 0]) > 0
        ),
        "description": "Should return a positive average value",
    },
    {
        "question": "Which loyalty tier has the most customers?",
        "check": lambda r: (
            r.get("data") is not None
            and any(tier in r["data"].to_string().lower() for tier in ["bronze", "silver", "gold"])
        ),
        "description": "Should reference loyalty tiers",
    },
    {
        "question": "How are we doing?",
        "check": lambda r: r.get("answer") is not None and len(r["answer"]) > 20,
        "description": "Ambiguous question should get a substantive response (clarification or overview)",
    },
]


def run_tests():
    passed = 0
    failed = 0
    for i, test in enumerate(TESTS, 1):
        print(f"\n[{i}/{len(TESTS)}] {test['question']}")
        print(f"  Expected: {test['description']}")
        try:
            result = ask(test["question"])
            if test["check"](result):
                print(f"  ✓ PASSED")
                passed += 1
            else:
                print(f"  ✗ FAILED")
                print(f"    SQL: {result.get('sql')}")
                print(f"    Answer: {result.get('answer', '')[:200]}")
                if result.get("data") is not None:
                    print(f"    Data:\n{result['data'].head().to_string()}")
                failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"Results: {passed}/{passed+failed} passed")
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
