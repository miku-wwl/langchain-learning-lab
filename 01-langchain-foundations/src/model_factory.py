"""One local LangChain model entry point for all 01 examples."""

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


def local_model_config(preferred_alias: str = "phi-4-mini") -> tuple[str, str]:
    """Return (OpenAI-compatible base URL, loaded model ID)."""
    base_url = os.getenv("LOCAL_LLM_BASE_URL")
    model_id = os.getenv("LOCAL_LLM_MODEL")
    if not base_url:
        status = _foundry_json("server", "status")
        if not status.get("running") or not status.get("webUrls"):
            raise RuntimeError("Foundry Local server is not running")
        base_url = status["webUrls"][0].rstrip("/") + "/v1"
    if not model_id:
        loaded = _foundry_json("model", "list", "--loaded")["models"]
        models = [model for model in loaded if model.get("type") == "Chat"]
        if not models:
            raise RuntimeError("No local chat model loaded; run 'foundry model load phi-4-mini'")
        preferred = next((m for m in models if m.get("alias") == preferred_alias), None)
        if preferred is None:
            raise RuntimeError(f"Local model '{preferred_alias}' is not loaded")
        model_id = preferred["id"]
    return base_url, model_id


def create_local_model(preferred_alias: str = "phi-4-mini") -> ChatOpenAI:
    # Windows shells can default to cp1252 even when a model replies in Chinese.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    base_url, model_id = local_model_config(preferred_alias)
    return ChatOpenAI(
        model=model_id,
        base_url=base_url,
        api_key="local",
        temperature=0,
        max_tokens=192,
        max_retries=0,
        timeout=120,
    )
