"""Stage B: load a local text file into LangChain Document objects."""

from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document


FAQ_PATH = Path(__file__).resolve().parents[1] / "resources" / "company_faq.txt"


def load_documents() -> list[Document]:
    return TextLoader(str(FAQ_PATH), encoding="utf-8").load()


def run() -> None:
    documents = load_documents()
    assert len(documents) == 1
    document = documents[0]
    assert isinstance(document, Document)
    assert all(section in document.page_content for section in ["Refund policy", "Delivery", "Membership", "Support"])
    assert Path(document.metadata["source"]).resolve() == FAQ_PATH
    print(f"DOCUMENT_COUNT={len(documents)}")
    print(f"DOCUMENT_TYPE={type(document).__name__}")
    print(f"DOCUMENT_METADATA={document.metadata}")
    print(f"DOCUMENT_CONTENT=\n{document.page_content}")
    print("DOCUMENT_LOADER=PASS")


if __name__ == "__main__":
    run()
