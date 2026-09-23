from router import classify_query
from stage_g_multi_delegate import QUERY


def test_router_selects_one_route_for_cross_domain_request():
    assert classify_query(QUERY) == "record"
    assert "ask_doctor_agent" in QUERY
