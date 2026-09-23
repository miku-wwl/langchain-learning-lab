"""Stage H: replay reruns only nodes after the selected checkpoint."""

from typing_extensions import NotRequired, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from stage_c_checkpointer import config


class TravelState(TypedDict):
    topic: NotRequired[str]
    output: NotRequired[str]


def build_graph():
    counts = {"choose_topic": 0, "build_output": 0}

    def choose_topic(state: TravelState) -> dict:
        counts["choose_topic"] += 1
        return {"topic": "cloud"}

    def build_output(state: TravelState) -> dict:
        counts["build_output"] += 1
        return {"output": f"topic={state['topic']}"}

    builder = StateGraph(TravelState)
    builder.add_node("choose_topic", choose_topic)
    builder.add_node("build_output", build_output)
    builder.add_edge(START, "choose_topic")
    builder.add_edge("choose_topic", "build_output")
    builder.add_edge("build_output", END)
    return builder.compile(checkpointer=InMemorySaver()), counts


def run() -> dict[str, object]:
    graph, counts = build_graph()
    original = graph.invoke({}, config("replay"))
    history = list(graph.get_state_history(config("replay")))
    before_output = next(snapshot for snapshot in history if snapshot.next == ("build_output",))
    assert original["output"] == "topic=cloud"
    assert counts == {"choose_topic": 1, "build_output": 1}
    replayed = graph.invoke(None, before_output.config)
    assert replayed["output"] == "topic=cloud"
    assert counts == {"choose_topic": 1, "build_output": 2}
    print(f"replay checkpoint={before_output.config['configurable']['checkpoint_id']}; counts={counts}")
    print("REPLAY_PASS")
    return {"graph": graph, "counts": counts, "original": original, "replayed": replayed}


if __name__ == "__main__":
    run()
