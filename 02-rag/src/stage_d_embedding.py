"""Stage D: generate real vectors and compare semantic similarity."""

from math import sqrt

from embedding_factory import EMBEDDING_MODEL, create_local_embeddings


def cosine_similarity(left: list[float], right: list[float]) -> float:
    assert len(left) == len(right) and left
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = sqrt(sum(a * a for a in left))
    right_norm = sqrt(sum(b * b for b in right))
    return dot / (left_norm * right_norm)


def run() -> None:
    embeddings = create_local_embeddings()
    query = embeddings.embed_query("How can I get a refund?")
    refund, weather = embeddings.embed_documents(
        ["What is the refund policy?", "The weather is sunny today."]
    )
    related = cosine_similarity(query, refund)
    unrelated = cosine_similarity(query, weather)
    assert len(query) > 0 and len(query) == len(refund) == len(weather)
    assert related > unrelated, (related, unrelated)
    print(f"EMBEDDING_MODEL={EMBEDDING_MODEL}")
    print(f"VECTOR_DIMENSION={len(query)} FIRST_8={query[:8]}")
    print(f"SIMILARITY_REFUND={related:.4f} SIMILARITY_WEATHER={unrelated:.4f}")
    print("LOCAL_EMBEDDING_SEMANTIC_SIMILARITY=PASS")


if __name__ == "__main__":
    run()
