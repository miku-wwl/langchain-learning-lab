"""Chapter-local discovery of a cached Foundry Local tool-capable model."""

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
        timeout=15,
    )
    return json.loads(result.stdout)


def local_chat_config(alias: str = "qwen3-4b") -> tuple[str, str]:
    base_url = os.getenv("LOCAL_OPENAI_BASE_URL")
    model_id = os.getenv("LOCAL_CHAT_MODEL")
    if not base_url:
        status = _foundry_json("server", "status")
        if not status.get("running") or not status.get("webUrls"):
            raise RuntimeError("Foundry Local server is not running")
        base_url = status["webUrls"][0].rstrip("/") + "/v1"
    if not model_id:
        loaded = _foundry_json("model", "list", "--loaded")["models"]
        selected = next((model for model in loaded if model.get("alias") == alias), None)
        if selected is None or not selected.get("supportsToolCalling"):
            raise RuntimeError(f"Load cached tool-capable model: foundry model load {alias}")
        model_id = selected["id"]
    return base_url, model_id


def create_local_model(*, alias: str = "qwen3-4b", max_tokens: int = 256) -> ChatOpenAI:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    base_url, model_id = local_chat_config(alias)
    return ChatOpenAI(
        model=model_id,
        base_url=base_url,
        api_key="local",
        temperature=0,
        max_tokens=max_tokens,
        max_retries=0,
        timeout=120,
    )
