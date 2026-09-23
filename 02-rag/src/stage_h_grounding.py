"""Stage H: known, paraphrased, and unknown questions through the same RAG."""

from model_factory import create_local_chat_model
from stage_e_vectorstore import REFUND_QUERY
from stage_f_retriever import build_retriever
from stage_g_rag import answer_question


PARAPHRASE_QUERY = "Once you approve my return, when should I see the money again?"
UNKNOWN_QUERY = "Who is the CEO of Northstar Shop?"


def has_refund_timing(documents: list) -> bool:
    return any("3 to 5 business days" in doc.page_content for doc in documents)


def says_unknown(answer: str) -> bool:
    lowered = answer.lower()
    return any(
        phrase in lowered
        for phrase in [
            "cannot answer",
            "don't know",
            "do not know",
            "not provided",
            "not mentioned",
            "insufficient",
            "no information",
        ]
    )


def run() -> None:
    retriever, _, _ = build_retriever()
    llm = create_local_chat_model()
    for label, question in [
        ("KNOWN", REFUND_QUERY),
        ("PARAPHRASE", PARAPHRASE_QUERY),
        ("UNKNOWN", UNKNOWN_QUERY),
    ]:
        documents, _, response = answer_question(question, retriever, llm)
        answer = str(response.content)
        print(f"{label}_QUESTION={question}")
        print(f"{label}_TOP_K={[doc.page_content for doc in documents]}")
        print(f"{label}_ANSWER={answer}")
        if label == "UNKNOWN":
            assert all("CEO" not in doc.page_content for doc in documents)
            assert says_unknown(answer), answer
        else:
            assert has_refund_timing(documents), f"{label} retrieval missed evidence"
            assert "3 to 5" in answer or "3-5" in answer, answer
        print(f"{label}_GROUNDING=PASS")

    print("THREE_QUESTION_GROUNDING=PASS")


if __name__ == "__main__":
    run()
