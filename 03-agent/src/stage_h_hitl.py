"""Stage H: local approval gate around a simulated SQL tool."""

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain.tools import tool
from langchain_core.messages import ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from model_factory import create_local_model


READS: list[str] = []
SIMULATED_SQL_CALLS: list[str] = []
HITL_POLICY = {
    "read_data": False,
    "execute_sql": {"allowed_decisions": ["approve", "reject"]},
}


@tool
def read_data(key: str) -> str:
    """Read a harmless value from an in-memory teaching example."""
    READS.append(key)
    return f"value for {key}"


@tool
def execute_sql(query: str) -> str:
    """Simulate SQL execution without connecting to a database."""
    SIMULATED_SQL_CALLS.append(query)
    return f"SIMULATED SQL: {query}"


def make_agent():
    return create_agent(
        model=create_local_model(max_tokens=256, alias="qwen2.5-0.5b"),
        tools=[read_data, execute_sql],
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on=HITL_POLICY,
                description_prefix="Tool execution pending approval",
            )
        ],
        checkpointer=InMemorySaver(),
        system_prompt="Use the named tool requested by the user. SQL is only simulated. /no_think",
    )


def run() -> None:
    agent = make_agent()
    safe_config = {"configurable": {"thread_id": "03-hitl-safe"}}
    safe = agent.invoke(
        {"messages": [{"role": "user", "content": "Use read_data with key=course. /no_think"}]},
        config=safe_config,
        version="v2",
    )
    print(f"SAFE_INTERRUPTS={safe.interrupts}")
    print(f"SAFE_READS={READS}")
    print(f"SAFE_MESSAGES={[(type(msg).__name__, str(msg.content)[:400], getattr(msg, 'tool_calls', None)) for msg in safe.value['messages']]}")
    assert not safe.interrupts
    assert READS == ["course"]
    assert any(isinstance(msg, ToolMessage) and "value for course" in str(msg.content) for msg in safe.value["messages"])
    print("HITL_SAFE_TOOL_NO_APPROVAL=PASS")

    approve_config = {"configurable": {"thread_id": "03-hitl-approve"}}
    proposed = agent.invoke(
        {"messages": [{"role": "user", "content": "Use execute_sql with query 'UPDATE demo SET flag=1'. /no_think"}]},
        config=approve_config,
        version="v2",
    )
    print(f"APPROVE_INTERRUPTS={proposed.interrupts}")
    assert proposed.interrupts
    assert SIMULATED_SQL_CALLS == [], "Approval gate must stop before tool execution"
    approved = agent.invoke(
        Command(resume={"decisions": [{"type": "approve"}]}),
        config=approve_config,
        version="v2",
    )
    print(f"APPROVED_SQL_CALLS={SIMULATED_SQL_CALLS}")
    print(f"APPROVED_INTERRUPTS={approved.interrupts}")
    assert not approved.interrupts
    assert len(SIMULATED_SQL_CALLS) == 1
    assert any(isinstance(msg, ToolMessage) and "SIMULATED SQL:" in str(msg.content) for msg in approved.value["messages"])
    print("HITL_APPROVE=PASS")

    reject_config = {"configurable": {"thread_id": "03-hitl-reject"}}
    proposed_reject = agent.invoke(
        {"messages": [{"role": "user", "content": "Use execute_sql with query 'DROP TABLE demo'. /no_think"}]},
        config=reject_config,
        version="v2",
    )
    print(f"REJECT_INTERRUPTS={proposed_reject.interrupts}")
    assert proposed_reject.interrupts
    assert len(SIMULATED_SQL_CALLS) == 1
    rejected = agent.invoke(
        Command(resume={"decisions": [{"type": "reject", "message": "Human reviewer rejected this simulated query."}]}),
        config=reject_config,
        version="v2",
    )
    print(f"REJECTED_SQL_CALLS={SIMULATED_SQL_CALLS}")
    print(f"REJECTED_TOOL_MESSAGES={[(msg.status, msg.content) for msg in rejected.value['messages'] if isinstance(msg, ToolMessage)]}")
    assert not rejected.interrupts
    assert len(SIMULATED_SQL_CALLS) == 1, "Rejected query must never reach execute_sql"
    assert any(isinstance(msg, ToolMessage) and "rejected" in str(msg.content).lower() for msg in rejected.value["messages"])
    print("HITL_REJECT=PASS")


if __name__ == "__main__":
    run()
