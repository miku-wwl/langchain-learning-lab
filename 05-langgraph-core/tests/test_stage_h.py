import pytest

from stage_h_command import build_graph


@pytest.mark.parametrize(
    "score, expected, destination",
    [(80, "pass", "pass_node"), (40, "fail", "fail_node")],
)
def test_command_updates_and_routes(score, expected, destination):
    result = build_graph().invoke({"score": score, "result": "", "destination": ""})
    assert (result["result"], result["destination"]) == (expected, destination)
