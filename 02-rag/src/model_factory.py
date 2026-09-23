"""Local chat model for the independent 02 RAG chapter."""

import json
import os
import subprocess
import sys

from langchain_openai import ChatOpenAI


def _foundry_json(*args: str) -> dict:
    result = subprocess.run(
        ["foundry", *args, "--output", "json"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def local_chat_config() -> tuple[str, str]:
    """Find the current OpenAI-compatible URL and a loaded Qwen3 model."""
    base_url = os.getenv("LOCAL_OPENAI_BASE_URL")
    model_id = os.getenv("LOCAL_CHAT_MODEL")
    if not base_url:
        status = _foundry_json("server", "status")
        if not status.get("running") or not status.get("webUrls"):
            raise RuntimeError("Foundry Local is not running")
        base_url = status["webUrls"][0].rstrip("/") + "/v1"
    if not model_id:
        loaded = _foundry_json("model", "list", "--loaded")["models"]
        qwen = next((m for m in loaded if m.get("alias") == "qwen3-4b"), None)
        if qwen is None:
            raise RuntimeError("Load the cached chat model: foundry model load qwen3-4b")
        model_id = qwen["id"]
    return base_url, model_id


def create_local_chat_model() -> ChatOpenAI:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    base_url, model_id = local_chat_config()
    return ChatOpenAI(
        model=model_id,
        base_url=base_url,
        api_key="local",
        temperature=0,
        max_tokens=256,
        max_retries=0,
        timeout=120,
    )
