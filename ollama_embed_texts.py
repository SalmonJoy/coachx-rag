import os
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"
TEXT_PATH = ROOT / "sample_embedding_text.txt"

DEFAULT_MODELS = [
    "embeddinggemma",
    "qwen3-embedding",
    "all-minilm",
    "nomic-embed-text",
    "mxbai-embed-large",
]


def bearer_token(value: str | None) -> str | None:
    if not value:
        return None

    stripped = value.strip()
    if stripped.lower().startswith("bearer "):
        return stripped.split(None, 1)[1].strip()

    return stripped


def load_env(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing .env file: {path}")

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


def load_text_lines(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Missing text file: {path}")

    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def configured_models() -> list[str]:
    raw = os.environ.get("OLLAMA_EMBED_MODELS", "")
    models = [model.strip() for model in raw.split(",") if model.strip()]
    return models or DEFAULT_MODELS


def short_error(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text[:300]

    if isinstance(payload, dict):
        message = payload.get("error") or payload.get("message")
        if message:
            return str(message)

    return str(payload)[:300]


def try_embed(
    label: str,
    base_url: str,
    path: str,
    model: str,
    texts: list[str],
    api_key: str | None = None,
) -> dict[str, Any] | None:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    body = {
        "model": model,
        "input": texts,
        "truncate": True,
    }

    try:
        response = requests.post(url, json=body, headers=headers, timeout=60)
    except requests.RequestException as exc:
        print(f"{label} / {model}: connection failed ({exc})")
        return None

    if response.status_code != 200:
        print(f"{label} / {model}: HTTP {response.status_code} ({short_error(response)})")
        return None

    payload = response.json()
    embeddings = payload.get("embeddings")
    if embeddings is None and isinstance(payload.get("data"), list):
        embeddings = [item.get("embedding") for item in payload["data"]]

    if not embeddings:
        print(f"{label} / {model}: no embeddings found in response")
        return None

    dimensions = len(embeddings[0])
    print(f"{label} / {model}: connected, {len(embeddings)} embeddings, {dimensions} dimensions")
    return payload


def main() -> None:
    load_env(ENV_PATH)

    texts = load_text_lines(TEXT_PATH)
    api_key = bearer_token(os.environ.get("OLLAMA_API_KEY"))
    local_base_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    models = configured_models()

    print(f"Loaded {len(texts)} text lines from {TEXT_PATH.name}")
    print(f"Trying models: {', '.join(models)}")
    if api_key:
        print(f"OLLAMA_API_KEY loaded ({len(api_key)} characters)")

    checks: list[tuple[str, str, str, str | None]] = [
        ("local native", local_base_url, "/api/embed", None),
        ("local OpenAI-compatible", local_base_url, "/v1/embeddings", None),
    ]

    if api_key:
        checks.append(("cloud native", "https://ollama.com", "/api/embed", api_key))
        checks.append(("cloud OpenAI-compatible", "https://ollama.com", "/v1/embeddings", api_key))
    else:
        print("OLLAMA_API_KEY not found; skipping cloud check")

    connected = False
    for label, base_url, path, key in checks:
        print(f"\nChecking {label} endpoint: {base_url.rstrip('/')}{path}")
        for model in models:
            payload = try_embed(label, base_url, path, model, texts, key)
            if payload is not None:
                connected = True

    if not connected:
        raise SystemExit("\nNo working Ollama embedding model was found.")


if __name__ == "__main__":
    main()
