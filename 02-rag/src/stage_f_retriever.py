"""Stage F: compare direct vector search with the Retriever interface."""

from stage_e_vectorstore import REFUND_QUERY, build_vector_store


def build_retriever(k: int = 3):
    store, chunks = build_vector_store()
    return store.as_retriever(search_kwargs={"k": k}), store, chunks


def run() -> None:
    retriever, store, _ = build_retriever()
    direct = store.similarity_search(REFUND_QUERY, k=3)
    retrieved = retriever.invoke(REFUND_QUERY)
    assert len(retrieved) == 3
    assert [doc.page_content for doc in retrieved] == [doc.page_content for doc in direct]
    assert any("3 to 5 business days" in doc.page_content for doc in retrieved)
    print(f"QUERY={REFUND_QUERY}")
    for rank, document in enumerate(retrieved, start=1):
        print(f"RETRIEVER_TOP_{rank}_METADATA={document.metadata}")
        print(f"RETRIEVER_TOP_{rank}_CONTENT={document.page_content!r}")
    print("RETRIEVER_MATCHES_DIRECT_SEARCH=PASS")


if __name__ == "__main__":
    run()
