"""Stage G: explicit retrieve -> context -> prompt -> local LLM pipeline."""

from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate

from model_factory import create_local_chat_model
from stage_e_vectorstore import REFUND_QUERY
from stage_f_retriever import build_retriever


UNKNOWN_SENTENCE = "I cannot answer from the provided knowledge base."


def rag_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Answer Northstar Shop questions using only the supplied context. "
                "If the context does not contain the answer, say: "
                f"'{UNKNOWN_SENTENCE}' "
                "Do not invent a policy or use outside knowledge.",
            ),
            ("user", "Context:\n{context}\n\nQuestion:\n{question}"),
        ]
    )


def format_docs(documents: list) -> str:
    return "\n\n".join(
        f"[source={Path(doc.metadata.get('source', 'unknown')).name}; "
        f"start_index={doc.metadata.get('start_index', 'unknown')}]\n{doc.page_content}"
        for doc in documents
    )


def answer_question(question: str, retriever=None, llm=None):
    if retriever is None:
        retriever, _, _ = build_retriever()
    if llm is None:
        llm = create_local_chat_model()
    documents = retriever.invoke(question)
    context = format_docs(documents)
    response = (rag_prompt() | llm).invoke({"context": context, "question": question})
    return documents, context, response


def run() -> None:
    documents, context, response = answer_question(REFUND_QUERY)
    assert any("3 to 5 business days" in doc.page_content for doc in documents)
    assert "3 to 5 business days" in context
    answer = str(response.content)
    print(f"QUESTION={REFUND_QUERY}")
    print(f"RETRIEVED_CHUNKS={len(documents)}")
    print(f"CONTEXT={context}")
    print(f"GROUNDED_ANSWER={answer}")
    assert "3 to 5" in answer or "3-5" in answer, answer
    print("TWO_STEP_RAG=PASS")


if __name__ == "__main__":
    run()
