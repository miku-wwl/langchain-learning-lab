"""Expose each specialist Agent as one high-level Supervisor tool."""

from langchain.tools import tool

from router_graph import scoped_task
from workers import invoke_worker


def create_subagent_tools(workers: dict, events: list[dict] | None = None) -> list:
    def capture(kind: str, original_task: str, worker_task: str, result: dict) -> None:
        if events is not None:
            events.append({
                "kind": kind,
                "supervisor_task": original_task,
                "worker_task": worker_task,
                "internal_tool": result["calls"][0]["name"],
                "worker_message_types": [type(message).__name__ for message in result["messages"]],
                "returned": result["filtered"],
            })

    @tool
    def ask_record_agent(task: str) -> str:
        """Delegate fictional user record-history tasks to the record specialist."""
        worker_task = scoped_task("record", task)
        result = invoke_worker(workers, "record", worker_task)
        capture("record", task, worker_task, result)
        return result["filtered"]

    @tool
    def ask_guideline_agent(task: str) -> str:
        """Delegate fictional educational guideline-note searches to the guideline specialist."""
        worker_task = scoped_task("guideline", task)
        result = invoke_worker(workers, "guideline", worker_task)
        capture("guideline", task, worker_task, result)
        return result["filtered"]

    @tool
    def ask_doctor_agent(task: str) -> str:
        """Delegate fictional doctor-directory lookups to the directory specialist."""
        worker_task = scoped_task("doctor", task)
        result = invoke_worker(workers, "doctor", worker_task)
        capture("doctor", task, worker_task, result)
        return result["filtered"]

    return [ask_record_agent, ask_guideline_agent, ask_doctor_agent]
