"""Stage D: inspect current and historical StateSnapshot objects."""

from stage_c_checkpointer import build_graph, config


def run() -> dict[str, object]:
    graph = build_graph()
    graph.invoke({"increment": 4}, config("inspect"))
    snapshot = graph.get_state(config("inspect"))
    assert snapshot.values["total"] == 4
    assert snapshot.next == ()
    checkpoint_id = snapshot.config["configurable"]["checkpoint_id"]
    assert checkpoint_id
    print(f"Current values={snapshot.values} next={snapshot.next} checkpoint_id={checkpoint_id}")
    print("STATE_INSPECTION_PASS")

    history = list(graph.get_state_history(config("inspect")))
    for item in history:
        print(f"checkpoint_id={item.config['configurable']['checkpoint_id']} next={item.next} values={item.values}")
    before_finish = next(item for item in history if item.next == ("finish",))
    assert before_finish.values["total"] == 4
    assert before_finish.config["configurable"]["checkpoint_id"] != checkpoint_id
    print("STATE_HISTORY_PASS")
    return {"graph": graph, "snapshot": snapshot, "history": history, "before_finish": before_finish}


if __name__ == "__main__":
    run()
