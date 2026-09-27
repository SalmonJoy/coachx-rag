import os
import sys
from pathlib import Path
from typing import Any

import requests
from pinecone import Pinecone


ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"

DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_OLLAMA_EMBED_MODEL = "nomic-embed-text"
DEFAULT_NAMESPACE = "coachx-sample"
DEFAULT_EXPECTED_DIMENSION = 768
DEFAULT_TOP_K = 3
DEFAULT_CHAT_BASE_URL = "https://ollama.com"
DEFAULT_CHAT_MODEL = "gpt-oss:20b-cloud"
DEFAULT_CHAT_PATH = "/api/chat"
DEFAULT_TEMPERATURE = 0.0
DEFAULT_NUM_PREDICT = 300


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def bearer_token(value: str | None) -> str | None:
    if not value:
        return None

    stripped = value.strip()
    if stripped.lower().startswith("bearer "):
        return stripped.split(None, 1)[1].strip()

    return stripped


def load_env(path: Path) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value or value.startswith("<"):
        raise RuntimeError(f"{name} is missing or still set to a placeholder in .env")
    return value


def env_value(name: str, default: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value or value.startswith("<"):
        return default
    return value


def int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw or raw.startswith("<"):
        return default

    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer, got {raw!r}") from exc

    if value <= 0:
        raise RuntimeError(f"{name} must be greater than 0")

    return value


def float_env(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw or raw.startswith("<"):
        return default

    try:
        return float(raw)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a number, got {raw!r}") from exc


def get_user_query() -> str:
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:]).strip()
    else:
        query = input("Enter your question: ").strip()

    if not query:
        raise RuntimeError("Question cannot be empty")

    return query


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


def embed_query(
    query: str,
    ollama_host: str,
    model: str,
    expected_dimension: int,
) -> list[float]:
    url = f"{ollama_host.rstrip('/')}/api/embed"
    body = {
        "model": model,
        "input": [query],
        "truncate": True,
    }

    try:
        response = requests.post(url, json=body, timeout=60)
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Could not connect to Ollama at {url}. Is Ollama running?"
        ) from exc

    if response.status_code != 200:
        raise RuntimeError(
            f"Ollama embed returned HTTP {response.status_code}: "
            f"{short_error(response)}"
        )

    payload = response.json()
    embeddings = payload.get("embeddings")
    if not embeddings:
        raise RuntimeError("Ollama embed response did not contain embeddings")

    vector = embeddings[0]
    if len(vector) != expected_dimension:
        raise RuntimeError(
            f"Query embedding has {len(vector)} dimensions, "
            f"expected {expected_dimension}"
        )

    return vector


def get_index_client(client: Pinecone, index_name: str) -> Any:
    if hasattr(client, "index"):
        return client.index(index_name)

    return client.Index(index_name)


def query_pinecone(
    api_key: str,
    index_name: str,
    namespace: str,
    query_vector: list[float],
    top_k: int,
) -> Any:
    try:
        client = Pinecone(api_key=api_key)
        index = get_index_client(client, index_name)
        return index.query(
            vector=query_vector,
            top_k=top_k,
            namespace=namespace,
            include_metadata=True,
            include_values=False,
        )
    except Exception as exc:
        raise RuntimeError(f"Pinecone query failed: {exc}") from exc


def response_matches(response: Any) -> list[Any]:
    if hasattr(response, "matches"):
        return list(response.matches or [])

    if isinstance(response, dict):
        return list(response.get("matches") or [])

    return []


def match_value(match: Any, key: str, default: Any = None) -> Any:
    if isinstance(match, dict):
        return match.get(key, default)

    return getattr(match, key, default)


def normalized_matches(matches: list[Any]) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    for match in matches:
        metadata = match_value(match, "metadata", {}) or {}
        text = str(metadata.get("text", "")).strip()
        chunks.append(
            {
                "id": match_value(match, "id", "<missing-id>"),
                "score": float(match_value(match, "score", 0.0) or 0.0),
                "text": text,
            }
        )

    return chunks


def build_context(chunks: list[dict[str, Any]]) -> str:
    parts = []
    for index, chunk in enumerate(chunks, start=1):
        parts.append(
            f"[Chunk {index}]\n"
            f"ID: {chunk['id']}\n"
            f"Score: {chunk['score']:.4f}\n"
            f"Text: {chunk['text']}"
        )

    return "\n\n".join(parts)


def call_gpt_oss(
    query: str,
    chunks: list[dict[str, Any]],
    api_key: str,
    base_url: str,
    path: str,
    model: str,
    temperature: float,
    num_predict: int,
) -> str:
    headers = {"Content-Type": "application/json"}
    token = bearer_token(api_key)
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    context = build_context(chunks)
    body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You answer questions using only the provided retrieved chunks. "
                    "If the chunks do not contain enough information, say that the "
                    "retrieved chunks do not provide enough information. Keep the "
                    "answer concise and mention the chunk IDs you used."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question:\n{query}\n\n"
                    f"Retrieved chunks:\n{context}\n\n"
                    "Provide a grounded answer based only on these chunks."
                ),
            },
        ],
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": num_predict,
        },
    }

    try:
        response = requests.post(url, json=body, headers=headers, timeout=120)
    except requests.RequestException as exc:
        raise RuntimeError(f"Could not connect to Ollama chat endpoint at {url}") from exc

    if response.status_code != 200:
        raise RuntimeError(
            f"Ollama chat returned HTTP {response.status_code}: "
            f"{short_error(response)}"
        )

    payload = response.json()
    if isinstance(payload.get("message"), dict):
        answer = str(payload["message"].get("content", "")).strip()
    elif isinstance(payload.get("choices"), list) and payload["choices"]:
        message = payload["choices"][0].get("message", {})
        answer = str(message.get("content", "")).strip()
    else:
        answer = ""

    if not answer:
        raise RuntimeError("Ollama chat response did not contain an answer")

    return answer


def print_sources(chunks: list[dict[str, Any]]) -> None:
    print("Retrieved source chunks:")
    for index, chunk in enumerate(chunks, start=1):
        print(f"{index}. ID: {chunk['id']}")
        print(f"   Score: {chunk['score']:.4f}")
        print(f"   Text: {chunk['text']}")
        print()


def main() -> None:
    print("[1/5] Loading configuration...")
    load_env(ENV_PATH)

    query = get_user_query()
    pinecone_api_key = required_env("PINECONE_API_KEY")
    index_name = required_env("PINECONE_INDEX_NAME")
    namespace = env_value("PINECONE_NAMESPACE", DEFAULT_NAMESPACE)
    ollama_host = env_value("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)
    embed_model = env_value("OLLAMA_EMBED_MODEL", DEFAULT_OLLAMA_EMBED_MODEL)
    expected_dimension = int_env(
        "PINECONE_EXPECTED_DIMENSION", DEFAULT_EXPECTED_DIMENSION
    )
    top_k = int_env("PINECONE_TOP_K", DEFAULT_TOP_K)
    ollama_api_key = required_env("OLLAMA_API_KEY")
    chat_base_url = env_value("OLLAMA_CHAT_BASE_URL", DEFAULT_CHAT_BASE_URL)
    chat_model = env_value("OLLAMA_CHAT_MODEL", DEFAULT_CHAT_MODEL)
    chat_path = env_value("OLLAMA_CHAT_PATH", DEFAULT_CHAT_PATH)
    temperature = float_env("OLLAMA_ANSWER_TEMPERATURE", DEFAULT_TEMPERATURE)
    num_predict = int_env("OLLAMA_ANSWER_NUM_PREDICT", DEFAULT_NUM_PREDICT)

    print(f"[2/5] Embedding question with {embed_model!r}...")
    query_vector = embed_query(query, ollama_host, embed_model, expected_dimension)
    print(f"      Query embedding dimensions: {len(query_vector)}")

    print(f"[3/5] Retrieving top {top_k} chunks from Pinecone...")
    response = query_pinecone(
        pinecone_api_key,
        index_name,
        namespace,
        query_vector,
        top_k,
    )
    chunks = normalized_matches(response_matches(response))
    if not chunks:
        raise RuntimeError("Pinecone returned no matching chunks")

    print("[4/5] Sending question and chunks to GPT-OSS...")
    answer = call_gpt_oss(
        query,
        chunks,
        ollama_api_key,
        chat_base_url,
        chat_path,
        chat_model,
        temperature,
        num_predict,
    )

    print("[5/5] Grounded answer:")
    print()
    print(answer)
    print()
    print_sources(chunks)


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, RuntimeError) as exc:
        raise SystemExit(f"Error: {exc}") from exc
