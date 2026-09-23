import pytest
from langgraph.errors import GraphRecursionError

from stage_e_routing_loop import build_counting_graph, build_routing_graph


@pytest.mark.parametrize("number, expected", [(5, "positive"), (-5, "negative")])
def test_conditional_route(number, expected):
    result = build_routing_graph().invoke({"number": number, "result": ""})
    assert result["result"] == expected


def test_loop_terminates():
    assert build_counting_graph().invoke({"count": 0}) == {"count": 3}


def test_recursion_guard():
    with pytest.raises(GraphRecursionError):
        build_counting_graph(always_continue=True).invoke(
            {"count": 0}, config={"recursion_limit": 4}
        )
