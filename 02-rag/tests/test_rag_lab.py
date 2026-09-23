from math import isfinite
from pathlib import Path
import sys
import pytest
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from stage_b_loader import FAQ_PATH, load_documents
from stage_c_splitter import CHUNK_SIZE, split_documents
from embedding_factory import create_local_embeddings
from stage_d_embedding import cosine_similarity
from stage_e_vectorstore import REFUND_QUERY

@pytest.fixture(scope="module")
def indexed_corpus():
    documents = load_documents()
    chunks = split_documents(documents)
    embeddings = create_local_embeddings()
    store = InMemoryVectorStore(embeddings)
    ids = store.add_documents(chunks)
    assert len(ids) == len(chunks)
    return documents, chunks, embeddings, store

def test_document_loader():
    documents = load_documents()
    assert len(documents) == 1 and isinstance(documents[0], Document)
    assert Path(documents[0].metadata["source"]).resolve() == FAQ_PATH
    assert all(topic in documents[0].page_content for topic in ["Refund policy", "Delivery", "Membership", "Support"])

def test_chunk_creation_and_source(indexed_corpus):
    documents, chunks, _, _ = indexed_corpus
    assert len(chunks) > len(documents)
    assert all(len(chunk.page_content) <= CHUNK_SIZE for chunk in chunks)
    assert all(chunk.metadata["source"] == str(FAQ_PATH) for chunk in chunks)
    assert all(isinstance(chunk.metadata["start_index"], int) for chunk in chunks)
    assert any("3 to 5 business days" in chunk.page_content for chunk in chunks)

def test_embedding_dimension_and_semantic_order(indexed_corpus):
    _, _, embeddings, _ = indexed_corpus
    query = embeddings.embed_query("How can I get a refund?")
    refund, weather = embeddings.embed_documents(["What is the refund policy?", "The weather is sunny today."])
    assert len(query) > 0 and len(query) == len(refund) == len(weather)
    assert all(isfinite(value) for value in query)
    assert cosine_similarity(query, refund) > cosine_similarity(query, weather)

def test_vector_store_search_and_scores(indexed_corpus):
    _, _, _, store = indexed_corpus
    results = store.similarity_search_with_score(REFUND_QUERY, k=3)
    assert len(results) == 3
    assert all(isinstance(doc, Document) and isfinite(score) for doc, score in results)
    assert any("3 to 5 business days" in doc.page_content for doc, _ in results)

def test_retriever_matches_direct_search(indexed_corpus):
    _, _, _, store = indexed_corpus
    retriever = store.as_retriever(search_kwargs={"k": 3})
    direct = store.similarity_search(REFUND_QUERY, k=3)
    assert [doc.page_content for doc in retriever.invoke(REFUND_QUERY)] == [doc.page_content for doc in direct]
