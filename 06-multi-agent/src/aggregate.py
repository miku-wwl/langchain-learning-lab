"""A deterministic final response stage for the one-worker Router pattern."""

from router_graph import MultiAgentState


def aggregate_result(state: MultiAgentState) -> dict:
    if state["route"] == "refuse":
        return {"final_answer": state["worker_result"]}
    return {"final_answer": f"SYNTHETIC {state['route'].upper()} RESULT: {state['worker_result']}"}
