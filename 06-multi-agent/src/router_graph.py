"""Pattern A: LangGraph routes one request to one real specialist agent."""

import re
from typing import Callable

from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph

from router import Route, classify_query
from workers import invoke_worker


class MultiAgentState(TypedDict):
    query: str
    route: str
    worker_name: str
    worker_tool: str
    worker_result: str
    final_answer: str


def initial_state(query: str) -> MultiAgentState:
    return {
        "query": query, "route": "", "worker_name": "", "worker_tool": "",
        "worker_result": "", "final_answer": "",
    }


def scoped_task(kind: str, query: str) -> str:
    if kind == "record":
        user_id = next(iter(re.findall(r"user_[A-Za-z0-9_]+", query)), "user_123")
        return f"Use get_history_records with user_id={user_id}. Summarize only fictional entries. /no_think"
    if kind == "guideline":
        return "Use search_demo_guideline with query=general. Summarize only fictional note. /no_think"
    specialty = "general"
    return f"Use find_demo_doctors with specialty={specialty}. List only fictional entries. /no_think"


def build_router_graph(workers: dict, aggregate_node: Callable | None = None):
    def router(state: MultiAgentState) -> dict:
        return {"route": classify_query(state["query"])}

    def choose(state: MultiAgentState) -> Route:
        return state["route"]  # type: ignore[return-value]

    def worker_node(kind: str):
        def run(state: MultiAgentState) -> dict:
            result = invoke_worker(workers, kind, scoped_task(kind, state["query"]))
            return {
                "worker_name": kind,
                "worker_tool": result["calls"][0]["name"],
                "worker_result": result["filtered"],
            }
        return run

    def refuse(state: MultiAgentState) -> dict:
        return {"worker_name": "refuse", "worker_result": "REFUSED: only fictional record, guideline-note and directory tasks are available."}

    builder = StateGraph(MultiAgentState)
    builder.add_node("router", router)
    for kind in ("record", "guideline", "doctor"):
        builder.add_node(kind, worker_node(kind))
    builder.add_node("refuse", refuse)
    builder.add_edge(START, "router")
    builder.add_conditional_edges("router", choose)
    if aggregate_node is not None:
        builder.add_node("aggregate", aggregate_node)
    for kind in ("record", "guideline", "doctor", "refuse"):
        builder.add_edge(kind, "aggregate" if aggregate_node is not None else END)
    if aggregate_node is not None:
        builder.add_edge("aggregate", END)
    return builder.compile()
