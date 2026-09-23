from aggregate import aggregate_result
from router_graph import initial_state


def test_aggregate_is_deterministic():
    state = initial_state("history")
    state.update({"route": "record", "worker_result": "SYNTHETIC RECORDS: one"})
    assert aggregate_result(state) == {"final_answer": "SYNTHETIC RECORD RESULT: SYNTHETIC RECORDS: one"}


def test_refusal_passes_through_aggregate():
    state = initial_state("weather")
    state.update({"route": "refuse", "worker_result": "REFUSED: domain only"})
    assert aggregate_result(state) == {"final_answer": "REFUSED: domain only"}
