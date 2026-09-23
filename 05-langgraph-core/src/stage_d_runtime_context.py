"""D: mutable State, read-only run Context, and execution Config differ."""

from typing_extensions import TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime


class MessageState(TypedDict):
    message: str


class RunContext(TypedDict):
    user_id: str


def build_graph(observed: list[dict] | None = None):
    def greet(
        state: MessageState,
        runtime: Runtime[RunContext],
        config: RunnableConfig,
    ) -> dict:
        user_id = runtime.context["user_id"]
        if observed is not None:
            observed.append(
                {"user_id": user_id, "recursion_limit": config["recursion_limit"]}
            )
        return {"message": f"hello {user_id}"}

    builder = StateGraph(MessageState, context_schema=RunContext)
    builder.add_node("greet", greet)
    builder.add_edge(START, "greet")
    builder.add_edge("greet", END)
    return builder.compile()


def run() -> None:
    observed: list[dict] = []
    result = build_graph(observed).invoke(
        {"message": ""},
        context={"user_id": "user-123"},
        config={"recursion_limit": 10},
    )
    print(f"RUNTIME_AND_CONFIG={observed}")
    print(f"RETURNED_STATE={result}")
    assert observed == [{"user_id": "user-123", "recursion_limit": 10}]
    assert result == {"message": "hello user-123"}
    assert "user_id" not in result
    print("RUNTIME_CONTEXT_PASS")


if __name__ == "__main__":
    run()
