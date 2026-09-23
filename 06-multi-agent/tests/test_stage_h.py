from router_graph import scoped_task


def test_scoped_task_drops_unrelated_context():
    original = "records for user_123; unrelated CANARY weather and directory trace"
    worker_task = scoped_task("record", original)
    assert "user_123" in worker_task
    assert all(item not in worker_task for item in ("CANARY", "weather", "directory"))
