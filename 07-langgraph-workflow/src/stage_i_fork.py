"""Stage I: update_state creates a new branch and keeps original history."""

from stage_c_checkpointer import config
from stage_h_replay import build_graph


def run() -> dict[str, object]:
    graph, counts = build_graph()
    original = graph.invoke({}, config("fork"))
    original_snapshot = graph.get_state(config("fork"))
    history = list(graph.get_state_history(config("fork")))
    before_output = next(snapshot for snapshot in history if snapshot.next == ("build_output",))
    fork_config = graph.update_state(before_output.config, values={"topic": "ai"}, as_node="choose_topic")
    assert fork_config["configurable"]["checkpoint_id"] != before_output.config["configurable"]["checkpoint_id"]
    forked = graph.invoke(None, fork_config)
    assert forked["output"] == "topic=ai"
    assert original["output"] == "topic=cloud"
    assert graph.get_state(original_snapshot.config).values["output"] == "topic=cloud"
    assert counts == {"choose_topic": 1, "build_output": 2}
    print(f"original={original['output']} fork={forked['output']} counts={counts}")
    print("FORK_PASS")
    print("ORIGINAL_HISTORY_PRESERVED_PASS")
    return {"graph": graph, "original": original, "forked": forked, "original_snapshot": original_snapshot}


if __name__ == "__main__":
    run()
