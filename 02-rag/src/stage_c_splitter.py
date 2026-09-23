"""Stage C: split Documents into Chunks while keeping source metadata."""

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from stage_b_loader import load_documents


CHUNK_SIZE = 180
CHUNK_OVERLAP = 25


def split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        add_start_index=True,
    )
    return splitter.split_documents(documents)


def run() -> None:
    documents = load_documents()
    chunks = split_documents(documents)
    assert len(chunks) > len(documents)
    assert all(chunk.metadata.get("source") == documents[0].metadata["source"] for chunk in chunks)
    assert all(isinstance(chunk.metadata.get("start_index"), int) for chunk in chunks)
    print(f"DOCUMENT_COUNT={len(documents)} CHUNK_COUNT={len(chunks)}")
    print(f"CHUNK_SIZE={CHUNK_SIZE} CHUNK_OVERLAP={CHUNK_OVERLAP}")
    for index, chunk in enumerate(chunks):
        print(f"CHUNK_{index}_LENGTH={len(chunk.page_content)} METADATA={chunk.metadata}")
        print(f"CHUNK_{index}_CONTENT={chunk.page_content!r}")

    # A short controlled example makes the overlap itself visible. Natural
    # paragraph boundaries may produce less than the target overlap.
    overlap_splitter = RecursiveCharacterTextSplitter(
        chunk_size=60, chunk_overlap=15, separators=[""]
    )
    pieces = overlap_splitter.split_text("0123456789" * 12)
    assert pieces[0][-15:] == pieces[1][:15]
    print(f"OVERLAP_EXAMPLE={pieces[0][-15:]} == {pieces[1][:15]}")
    print("TEXT_SPLITTER=PASS")


if __name__ == "__main__":
    run()
