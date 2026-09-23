"""B: route four classes without model variability."""

from router import classify_query


CASES = {
    "Show synthetic history records for user_123": "record",
    "Summarize the general demo guideline": "guideline",
    "List general demo doctors": "doctor",
    "What is the weather?": "refuse",
}


def run() -> None:
    for query, expected in CASES.items():
        actual = classify_query(query)
        assert actual == expected, (query, actual)
        print(f"ROUTE={actual} QUERY={query}")
    print("ROUTER_BASELINE_PASS")


if __name__ == "__main__":
    run()
