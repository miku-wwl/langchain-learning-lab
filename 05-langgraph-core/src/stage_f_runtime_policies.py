"""F: cache skips work, retry repeats a failure, handler changes the path."""

from typing import Literal

from typing_extensions import TypedDict

from langgraph.cache.memory import InMemoryCache
from langgraph.errors import NodeError
from langgraph.graph import END, START, StateGraph
from langgraph.types import CachePolicy, Command, RetryPolicy


class NumberState(TypedDict):
    number: int


class StatusState(TypedDict):
    status: str


FAST_RETRY = RetryPolicy(
    max_attempts=3,
    retry_on=ConnectionError,
    initial_interval=0.01,
    max_interval=0.01,
    jitter=False,
)


def build_cached_graph(calls: list[int]):
    def expensive(state: NumberState) -> dict:
        calls.append(state["number"])
        return {"number": state["number"] * 2}

    builder = StateGraph(NumberState)
    builder.add_node("expensive", expensive, cache_policy=CachePolicy(ttl=60))
    builder.add_edge(START, "expensive")
    builder.add_edge("expensive", END)
    return builder.compile(cache=InMemoryCache())


def build_retry_graph(attempts: list[int]):
    def flaky(state: StatusState) -> dict:
        attempts.append(len(attempts) + 1)
        if len(attempts) < 3:
            raise ConnectionError("transient local demonstration")
        return {"status": "ok"}

    builder = StateGraph(StatusState)
    builder.add_node("flaky", flaky, retry_policy=FAST_RETRY)
    builder.add_edge(START, "flaky")
    builder.add_edge("flaky", END)
    return builder.compile()


def build_handler_graph(attempts: list[int], observed_errors: list[str]):
    def always_fails(state: StatusState) -> dict:
        attempts.append(len(attempts) + 1)
        raise ConnectionError("permanent local demonstration")

    def on_error(
        state: StatusState, error: NodeError
    ) -> Command[Literal["fallback"]]:
        observed_errors.append(f"{error.node}:{type(error.error).__name__}")
        return Command(update={"status": "recovered"}, goto="fallback")

    def fallback(state: StatusState) -> dict:
        assert state["status"] == "recovered"
        return {"status": "fallback"}

    builder = StateGraph(StatusState)
    builder.add_node(
        "always_fails",
        always_fails,
        retry_policy=RetryPolicy(
            max_attempts=2,
            retry_on=ConnectionError,
            initial_interval=0.01,
            max_interval=0.01,
            jitter=False,
        ),
        error_handler=on_error,
        destinations=("fallback",),
    )
    builder.add_node("fallback", fallback)
    builder.add_edge(START, "always_fails")
    builder.add_edge("fallback", END)
    return builder.compile()


def run() -> None:
    cache_calls: list[int] = []
    cached = build_cached_graph(cache_calls)
    first = cached.invoke({"number": 5})
    second = cached.invoke({"number": 5})
    print(f"CACHE_RESULTS={first},{second} FUNCTION_CALLS={cache_calls}")
    assert first == second == {"number": 10} and cache_calls == [5]
    print("CACHE_PASS")

    retry_attempts: list[int] = []
    retried = build_retry_graph(retry_attempts).invoke({"status": "pending"})
    print(f"RETRY_RESULT={retried} ATTEMPTS={retry_attempts}")
    assert retried == {"status": "ok"} and retry_attempts == [1, 2, 3]
    print("RETRY_PASS")

    failure_attempts: list[int] = []
    errors: list[str] = []
    handled = build_handler_graph(failure_attempts, errors).invoke(
        {"status": "pending"}
    )
    print(f"HANDLED_RESULT={handled} ATTEMPTS={failure_attempts} ERRORS={errors}")
    assert handled == {"status": "fallback"}
    assert failure_attempts == [1, 2]
    assert errors == ["always_fails:ConnectionError"]
    print("ERROR_HANDLER_PASS")


if __name__ == "__main__":
    run()
