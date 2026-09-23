"""Pattern B: a create_agent supervisor delegates through high-level tools."""

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call
from langchain_core.messages import AIMessage, ToolMessage

from model_factory import create_local_model


def build_supervisor(wrappers: list, *, required_calls: int = 1):
    @wrap_model_call
    def require_delegation(request, handler):
        completed = sum(isinstance(message, ToolMessage) for message in request.messages)
        choice = "required" if completed < required_calls else "none"
        return handler(request.override(tool_choice=choice))

    return create_agent(
        model=create_local_model(), tools=wrappers, middleware=[require_delegation],
        system_prompt=(
            "You are a coordinator for fictional learning-lab data. Delegate domain work to "
            "specialists. History/records -> ask_record_agent ONLY. Guideline/guide -> "
            "ask_guideline_agent ONLY. Doctor/directory -> ask_doctor_agent ONLY. The only "
            "allowed evidence is what specialist tools return. For a request spanning domains, "
            "call every needed specialist; do not repeat a completed specialist. In the final "
            "reply copy the specialist results without adding claims. Name any error explicitly. "
            "Do not invent medical facts or advice. /no_think"
        ),
    )


def invoke_supervisor(agent, query: str) -> dict:
    result = agent.invoke({"messages": [{"role": "user", "content": query}]})
    messages = result["messages"]
    calls = [call for msg in messages if isinstance(msg, AIMessage) for call in msg.tool_calls]
    tool_messages = [msg for msg in messages if isinstance(msg, ToolMessage)]
    assert calls and tool_messages and isinstance(messages[-1], AIMessage)
    assert str(messages[-1].content).strip()
    return {"final": str(messages[-1].content), "calls": calls, "tool_messages": tool_messages, "messages": messages}
