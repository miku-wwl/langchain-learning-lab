"""K: end-to-end graph combining routing, dynamic tasks, reduction and streaming."""

import operator
from pathlib import Path
from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send


class FinalState(TypedDict):
    text: str
    normalized: str
    mode: str
    results: Annotated[list[str], operator.add]
    output: str


class WorkerInput(TypedDict):
    subject: str


def build_graph():
    def normalize(state: FinalState) -> dict:
        normalized = ",".join(part.strip().lower() for part in state["text"].split(","))
        return {"normalized": normalized, "mode": "fanout" if "," in normalized else "fast"}

    def route(state: FinalState) -> str | list[Send]:
        if state["mode"] == "fast":
            return "fast"
        return [Send("worker", {"subject": part}) for part in state["normalized"].split(",")]

    def fast(state: FinalState) -> dict:
        return {"results": [f"fast:{state['normalized']}"]}

    def worker(state: WorkerInput) -> dict:
        return {"results": [f"processed:{state['subject']}"]}

    def finalize(state: FinalState) -> dict:
        return {"output": " | ".join(sorted(state["results"]))}

    builder = StateGraph(FinalState)
    builder.add_node("normalize", normalize)
    builder.add_node("fast", fast)
    builder.add_node("worker", worker)
    builder.add_node("finalize", finalize)
    builder.add_edge(START, "normalize")
    builder.add_conditional_edges("normalize", route, ["fast", "worker"])
    builder.add_edge("fast", "finalize")
    builder.add_edge("worker", "finalize")
    builder.add_edge("finalize", END)
    return builder.compile()


def initial_state(text: str) -> FinalState:
    return {"text": text, "normalized": "", "mode": "", "results": [], "output": ""}


def run() -> None:
    graph = build_graph()
    fast = graph.invoke(initial_state("  Hello  "))
    fanout = graph.invoke(initial_state(" A, B, C "))
    assert fast["output"] == "fast:hello"
    assert fanout["output"] == "processed:a | processed:b | processed:c"
    assert set(fanout["results"]) == {"processed:a", "processed:b", "processed:c"}

    updates = list(graph.stream(initial_state(" X, Y "), stream_mode="updates"))
    assert any("normalize" in event for event in updates)
    assert any("worker" in event for event in updates)
    assert any("finalize" in event for event in updates)
    assert updates[-1]["finalize"]["output"] == "processed:x | processed:y"

    mermaid = graph.get_graph().draw_mermaid()
    assert "normalize" in mermaid and "finalize" in mermaid and "worker" in mermaid
    path = Path(__file__).resolve().parents[1] / "docs" / "final-graph.mmd"
    path.write_text(mermaid, encoding="utf-8")
    assert path.read_text(encoding="utf-8") == mermaid
    print(f"FINAL_FAST={fast['output']} FINAL_FANOUT={fanout['output']}")
    print(f"FINAL_STREAM={updates}")
    print(f"MERMAID_FILE={path}")
    print("FINAL_GRAPH_PASS")


if __name__ == "__main__":
    run()
