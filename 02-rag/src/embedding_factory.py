"""Local ONNX embeddings for the independent 02 RAG chapter."""

from pathlib import Path

from langchain_community.embeddings import FastEmbedEmbeddings


EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
MODEL_CACHE = Path(__file__).resolve().parents[1] / ".model_cache"


def create_local_embeddings() -> FastEmbedEmbeddings:
    return FastEmbedEmbeddings(
        model_name=EMBEDDING_MODEL,
        cache_dir=str(MODEL_CACHE),
        threads=2,
    )
