"""Stage A: raw updates, values, custom, and asynchronous values."""

import asyncio

from runtime_graph import build_graph, initial_state


async def _async_values() -> list[dict]:
    graph = build_graph()
    return [part["data"] async for part in graph.astream(initial_state(), stream_mode="values", version="v2")]


def run() -> dict[str, object]:
    graph = build_graph()
    updates = [part["data"] for part in graph.stream(initial_state(), stream_mode="updates", version="v2")]
    assert updates == [{"router": {"route": "worker"}}, {"worker": {"result": "handled:hello"}}]
    for update in updates:
        node, partial = next(iter(update.items()))
        print(f"Node={node} Partial State Update={partial}")
    print("RAW_STREAM_UPDATES_PASS")

    values = [part["data"] for part in graph.stream(initial_state(), stream_mode="values", version="v2")]
    assert values[-1] == {"query": "hello", "route": "worker", "result": "handled:hello"}
    assert any(value["route"] == "worker" and value["result"] == "" for value in values)
    assert asyncio.run(_async_values())[-1] == values[-1]
    print(f"Final State={values[-1]}")
    print("RAW_STREAM_VALUES_PASS")

    custom = [part["data"] for part in graph.stream(initial_state(), stream_mode="custom", version="v2")]
    assert custom == [{"stage": "worker", "status": "started"}, {"stage": "worker", "status": "finished"}]
    print(f"Custom Events={custom}")
    print("RAW_STREAM_CUSTOM_PASS")
    return {"updates": updates, "values": values, "custom": custom}


if __name__ == "__main__":
    run()
