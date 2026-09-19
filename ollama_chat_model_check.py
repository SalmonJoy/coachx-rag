import os
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"

DEFAULT_MODELS = [
    "llama4:scout-cloud",
    "llama4:maverick-cloud",
    "llama3.3:70b-cloud",
    "qwen3:480b-cloud",
    "qwen3-coder:480b-cloud",
    "qwen3-vl:235b-cloud",
    "gpt-oss:20b-cloud",
    "gpt-oss:120b-cloud",
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


def configured_models() -> list[str]:
    raw = os.environ.get("OLLAMA_CHAT_MODELS", "")
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


def try_chat(
    label: str,
    base_url: str,
    path: str,
    model: str,
    api_key: str | None,
) -> dict[str, Any] | None:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    body = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "Reply with exactly: connected",
            }
        ],
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": 8,
        },
    }

    try:
        response = requests.post(url, json=body, headers=headers, timeout=90)
    except requests.RequestException as exc:
        print(f"{label} / {model}: connection failed ({exc})")
        return None

    if response.status_code != 200:
        print(f"{label} / {model}: HTTP {response.status_code} ({short_error(response)})")
        return None

    payload = response.json()
    content = ""
    if isinstance(payload.get("message"), dict):
        content = str(payload["message"].get("content", ""))
    elif isinstance(payload.get("choices"), list) and payload["choices"]:
        message = payload["choices"][0].get("message", {})
        content = str(message.get("content", ""))

    preview = " ".join(content.split())[:120]
    print(f"{label} / {model}: connected, response={preview!r}")
    return payload


def main() -> None:
    load_env(ENV_PATH)

    api_key = bearer_token(os.environ.get("OLLAMA_API_KEY"))
    if not api_key:
        raise SystemExit("OLLAMA_API_KEY was not found in .env or environment.")

    models = configured_models()
    print(f"OLLAMA_API_KEY loaded ({len(api_key)} characters)")
    print(f"Trying chat models: {', '.join(models)}")

    checks: list[tuple[str, str, str]] = [
        ("cloud native", "https://ollama.com", "/api/chat"),
        ("cloud OpenAI-compatible", "https://ollama.com", "/v1/chat/completions"),
    ]

    connected = False
    for label, base_url, path in checks:
        print(f"\nChecking {label} endpoint: {base_url.rstrip('/')}{path}")
        for model in models:
            payload = try_chat(label, base_url, path, model, api_key)
            if payload is not None:
                connected = True

    if not connected:
        raise SystemExit("\nNo working Ollama cloud chat model was found.")


if __name__ == "__main__":
    main()
