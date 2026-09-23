from math import isfinite
from pathlib import Path
import sys
import pytest
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from stage_b_loader import FAQ_PATH, load_documents

def test_document_loader():
    documents = load_documents()
    assert len(documents) == 1 and isinstance(documents[0], Document)
    assert Path(documents[0].metadata["source"]).resolve() == FAQ_PATH
    assert all(topic in documents[0].page_content for topic in ["Refund policy", "Delivery", "Membership", "Support"])
