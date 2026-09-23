"""Stage D: a tool exception becomes an error ToolMessage."""

from langchain.agents import create_agent
from langchain.agents.middleware import ToolErrorMiddleware
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool

from model_factory import create_local_model


DIVIDE_ATTEMPTS: list[tuple[int, int]] = []
ERRORS_HANDLED: list[str] = []


@tool
def divide(a: int, b: int) -> float:
    """Divide integer a by integer b; zero is invalid."""
    DIVIDE_ATTEMPTS.append((a, b))
    if b == 0:
        raise ZeroDivisionError("b must not be zero")
    return a / b


def on_tool_error(exc: Exception, request: object) -> str:
    ERRORS_HANDLED.append(type(exc).__name__)
    return f"{type(exc).__name__}: {exc}. Explain why division by zero is invalid."


def run() -> None:
    agent = create_agent(
        model=create_local_model(),
        tools=[divide],
        middleware=[ToolErrorMiddleware(on_error=on_tool_error)],
        system_prompt="Use divide for division. If it fails, explain the error briefly. /no_think",
    )
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "Call divide with a=1 and b=0, then explain the result. /no_think"}]}
    )
    messages = result["messages"]
    print(f"ERROR_MESSAGE_TYPES={[type(msg).__name__ for msg in messages]}")
    print(f"DIVIDE_ATTEMPTS={DIVIDE_ATTEMPTS}")
    print(f"ERRORS_HANDLED={ERRORS_HANDLED}")
    print(f"TOOL_MESSAGES={[(msg.status, msg.content) for msg in messages if isinstance(msg, ToolMessage)]}")
    assert DIVIDE_ATTEMPTS == [(1, 0)], "The failed tool should execute exactly once; this stage does not retry"
    assert ERRORS_HANDLED == ["ZeroDivisionError"]
    tool_errors = [msg for msg in messages if isinstance(msg, ToolMessage) and msg.status == "error"]
    assert len(tool_errors) == 1 and "ZeroDivisionError" in str(tool_errors[0].content)
    assert isinstance(messages[-1], AIMessage) and messages[-1].content
    print(f"FINAL_AI_MESSAGE={messages[-1].content}")
    print("TOOL_ERROR_MIDDLEWARE=PASS")


if __name__ == "__main__":
    run()
