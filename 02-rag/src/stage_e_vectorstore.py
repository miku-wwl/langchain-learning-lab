"""Stage E: index chunks in memory and inspect semantic search results."""

from langchain_core.vectorstores import InMemoryVectorStore

from embedding_factory import create_local_embeddings
from stage_b_loader import load_documents
from stage_c_splitter import split_documents


REFUND_QUERY = "After a refund is approved, how long until the money is back?"


def build_vector_store(embeddings=None) -> tuple[InMemoryVectorStore, list]:
    chunks = split_documents(load_documents())
    store = InMemoryVectorStore(embeddings or create_local_embeddings())
    ids = store.add_documents(chunks)
    assert len(ids) == len(chunks)
    return store, chunks


def run() -> None:
    store, chunks = build_vector_store()
    results = store.similarity_search_with_score(REFUND_QUERY, k=3)
    assert len(results) == 3
    assert any("3 to 5 business days" in doc.page_content for doc, _ in results)
    print(f"INDEXED_CHUNKS={len(chunks)} QUERY={REFUND_QUERY}")
    for rank, (document, score) in enumerate(results, start=1):
        print(f"TOP_{rank}_SCORE={score:.4f} METADATA={document.metadata}")
        print(f"TOP_{rank}_CONTENT={document.page_content!r}")
    print("INMEMORY_VECTORSTORE_SIMILARITY_SEARCH=PASS")


if __name__ == "__main__":
    run()
