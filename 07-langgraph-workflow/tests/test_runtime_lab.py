"""Deterministic regression checks for each executed learning stage."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from stage_a_raw_streaming import run as stage_a
from stage_b_event_streaming import run as stage_b
from stage_c_checkpointer import run as stage_c
from stage_d_state_history import run as stage_d
from stage_e_store import run as stage_e
from stage_f_hitl import run as stage_f
from stage_g_resume_semantics import run as stage_g
from stage_h_replay import run as stage_h
from stage_i_fork import run as stage_i
from stage_j_multi_agent_runtime import run as stage_j
from stage_k_multi_agent_hitl_time_travel import run as stage_k
from stage_l_final_runtime import run as stage_l


def test_raw_stream_updates_values_custom_and_async():
    result = stage_a()
    assert len(result["updates"]) == 2
    assert result["custom"][0]["status"] == "started"


def test_typed_event_stream_and_subgraph():
    result = stage_b()
    assert result["output"]["result"] == "handled:hello"
    assert result["subgraphs"]


def test_checkpoint_and_thread_isolation():
    result = stage_c()
    assert result["second"]["total"] == 5
    assert result["other"]["total"] == 7


def test_state_and_history_inspection():
    result = stage_d()
    assert result["before_finish"].next == ("finish",)
    assert result["snapshot"].config["configurable"]["checkpoint_id"]


def test_store_shared_but_checkpoints_isolated():
    result = stage_e()
    assert result["a"]["thread_label"] != result["b"]["thread_label"]
    assert result["a"]["preference"] == result["b"]["preference"]


def test_interrupt_approve_and_reject():
    result = stage_f()
    assert result["results"]["hitl-approve"]["result"] == "SIMULATED_WRITE"
    assert result["results"]["hitl-reject"]["result"] == "REJECTED"


def test_resume_restarts_node_and_action_boundary():
    result = stage_g()
    assert result["approval_node_runs"] == 2
    assert len(result["bad_events"]) == 2
    assert len(result["good_events"]) == 1


def test_replay_only_reruns_future_node():
    assert stage_h()["counts"] == {"choose_topic": 1, "build_output": 2}


def test_fork_preserves_original_history():
    result = stage_i()
    assert result["original_snapshot"].values["output"] == "topic=cloud"
    assert result["forked"]["output"] == "topic=ai"


def test_multi_agent_streaming_and_persistence():
    result = stage_j()
    assert result["snapshot"].values["route"] == "record"
    assert len(result["custom"]) == 4


def test_multi_agent_hitl_and_route_fork():
    result = stage_k()
    assert result["outcomes"]["risk-reject"]["worker_result"] == "SIMULATED_SAFE_FALLBACK"
    assert result["forked"]["route"] == "doctor"


def test_final_integrated_runtime():
    result = stage_l()
    assert result["pause"].next == ("approval",)
    assert result["replay"]["worker_result"] == "SIMULATED_SAFE_FALLBACK"
    assert result["forked"]["route"] == "doctor"
