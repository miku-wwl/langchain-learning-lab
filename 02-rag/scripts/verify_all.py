"""Run all local RAG stages and print one evidence-backed status."""

import importlib.metadata
import os
from pathlib import Path
import subprocess
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB_ROOT / "src"))

from model_factory import local_chat_config  # noqa: E402


STAGES = [
    ("Local Chat Model", "stage_a_baseline.py", ["BASELINE_LOCAL_MODEL=PASS"]),
    ("Document Loader", "stage_b_loader.py", ["DOCUMENT_LOADER=PASS"]),
    ("Text Splitter", "stage_c_splitter.py", ["TEXT_SPLITTER=PASS"]),
    ("Local Embedding", "stage_d_embedding.py", ["LOCAL_EMBEDDING_SEMANTIC_SIMILARITY=PASS"]),
    ("InMemory Vector Store", "stage_e_vectorstore.py", ["INMEMORY_VECTORSTORE_SIMILARITY_SEARCH=PASS"]),
    ("Retriever", "stage_f_retriever.py", ["RETRIEVER_MATCHES_DIRECT_SEARCH=PASS"]),
    ("2-Step RAG", "stage_g_rag.py", ["TWO_STEP_RAG=PASS"]),
    (
        "Grounding (3 questions)",
        "stage_h_grounding.py",
        ["KNOWN_GROUNDING=PASS", "PARAPHRASE_GROUNDING=PASS", "UNKNOWN_GROUNDING=PASS"],
    ),
]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 48)
    print("LangChain 02 RAG E2E Verification")
    print("=" * 48)
    try:
        base_url, model_id = local_chat_config()
        assert importlib.metadata.version("langchain") == "1.4.2"
        for package in ["langchain-community", "langchain-text-splitters", "fastembed"]:
            importlib.metadata.version(package)
        print("Environment ..................... PASS")
        print(f"  Python {sys.version.split()[0]}; LangChain {importlib.metadata.version('langchain')}")
        print(f"  Chat model {model_id}; endpoint {base_url}")
        print(f"  Embedding package fastembed {importlib.metadata.version('fastembed')}")
    except Exception as exc:
        print(f"Environment ..................... BLOCKED: {exc}")
        print("BLOCKED")
        return 1

    failed = []
    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["LANGSMITH_TRACING"] = "false"
    environment["LANGCHAIN_TRACING_V2"] = "false"
    for name, script, required in STAGES:
        command = [sys.executable, str(LAB_ROOT / "src" / script)]
        try:
            result = subprocess.run(
                command,
                cwd=LAB_ROOT,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=180,
            )
            passed = result.returncode == 0 and all(token in result.stdout for token in required)
            print(f"{name:.<33} {'PASS' if passed else 'PARTIAL'}")
            if name == "Local Embedding":
                print(f"{'Semantic Similarity':.<33} {'PASS' if passed else 'PARTIAL'}")
            if name == "InMemory Vector Store":
                print(f"{'Similarity Search':.<33} {'PASS' if passed else 'PARTIAL'}")
            if name == "Grounding (3 questions)":
                for label, token in [
                    ("Known Question", "KNOWN_GROUNDING=PASS"),
                    ("Paraphrase Question", "PARAPHRASE_GROUNDING=PASS"),
                    ("Unknown Question", "UNKNOWN_GROUNDING=PASS"),
                ]:
                    item_passed = result.returncode == 0 and token in result.stdout
                    print(f"{label:.<33} {'PASS' if item_passed else 'PARTIAL'}")
            for line in result.stdout.splitlines():
                if line.strip():
                    print(f"  {line}")
            if not passed:
                failed.append(name)
                for line in result.stderr.splitlines()[-12:]:
                    print(f"  ERROR: {line}")
        except subprocess.TimeoutExpired:
            failed.append(name)
            print(f"{name:.<33} PARTIAL (timeout after 180s)")

    print("Redis Vector Store .............. OPTIONAL / NOT RUN")
    print("-" * 48)
    print("02_RAG_PASS_LOCAL" if not failed else f"PARTIAL: {', '.join(failed)}")
    print("=" * 48)
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
