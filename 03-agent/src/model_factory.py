"""Independent Foundry Local model discovery for chapter 03."""

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


def local_chat_config(alias: str = "qwen3-4b") -> tuple[str, str]:
    """Return the current local /v1 address and selected loaded model ID."""
    base_url = os.getenv("LOCAL_OPENAI_BASE_URL")
    model_id = os.getenv("LOCAL_CHAT_MODEL")
    if not base_url:
        status = _foundry_json("server", "status")
        if not status.get("running") or not status.get("webUrls"):
            raise RuntimeError("Foundry Local is not running")
        base_url = status["webUrls"][0].rstrip("/") + "/v1"
    if not model_id:
        loaded = _foundry_json("model", "list", "--loaded")["models"]
        model = next((item for item in loaded if item.get("alias") == alias), None)
        if model is None:
            raise RuntimeError(f"Load the cached local model: foundry model load {alias}")
        if not model.get("supportsToolCalling"):
            raise RuntimeError("Selected model does not advertise tool calling")
        model_id = model["id"]
    return base_url, model_id


def create_local_model(*, max_tokens: int = 256, alias: str = "qwen3-4b") -> ChatOpenAI:
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
