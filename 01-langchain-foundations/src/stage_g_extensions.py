"""Stage G: two small harness extensions mentioned by the syllabus."""

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, dynamic_prompt
from langchain.agents.structured_output import ToolStrategy
from pydantic import BaseModel

from model_factory import create_local_model


class Person(BaseModel):
    """A person extracted from text."""

    name: str
    age: int


MIDDLEWARE_CALLS: list[int] = []


@dynamic_prompt
def teaching_prompt(request: ModelRequest) -> str:
    MIDDLEWARE_CALLS.append(len(request.messages))
    return "Answer the user briefly. This system prompt was supplied by middleware."


def run() -> None:
    middleware_agent = create_agent(
        model=create_local_model(), tools=[], middleware=[teaching_prompt]
    )
    middleware_result = middleware_agent.invoke(
        {"messages": [{"role": "user", "content": "Say hello."}]}
    )
    assert MIDDLEWARE_CALLS, "dynamic prompt middleware was not called"
    assert middleware_result["messages"][-1].content
    print(f"MIDDLEWARE_CALLS={MIDDLEWARE_CALLS}")
    print(f"MIDDLEWARE_ANSWER={middleware_result['messages'][-1].content}")

    structured_model = create_local_model()
    structured_prompt = "Extract a Person from the user text using the response schema tool."
    if "qwen3" in structured_model.model_name.lower():
        structured_prompt += " /no_think"
    structured_agent = create_agent(
        model=structured_model,
        tools=[],
        response_format=ToolStrategy(Person),
        system_prompt=structured_prompt,
    )
    structured_result = structured_agent.invoke(
        {"messages": [{"role": "user", "content": "Alice is 30 years old."}]},
        config={"recursion_limit": 8},
    )
    person = structured_result["structured_response"]
    print(f"STRUCTURED_RESPONSE={person}")
    assert isinstance(person, Person)
    assert person.name == "Alice" and person.age == 30
    print("MIDDLEWARE_AND_STRUCTURED_OUTPUT=PASS")


if __name__ == "__main__":
    run()
