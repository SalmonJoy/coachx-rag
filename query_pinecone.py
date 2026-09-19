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
            f"Ollama returned HTTP {response.status_code}: {short_error(response)}"
        )

    payload = response.json()
    embeddings = payload.get("embeddings")
    if not embeddings:
        raise RuntimeError("Ollama response did not contain embeddings")

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


def print_matches(matches: list[Any], requested_count: int) -> None:
    if not matches:
        print("No matching chunks found.")
        return

    print(f"Top {min(requested_count, len(matches))} matching chunks:\n")
    for index, match in enumerate(matches, start=1):
        match_id = match_value(match, "id", "<missing-id>")
        score = match_value(match, "score", 0.0)
        metadata = match_value(match, "metadata", {}) or {}
        text = metadata.get("text", "<missing text metadata>")

        print(f"{index}. ID: {match_id}")
        print(f"   Score: {score:.4f}")
        print(f"   Text: {text}")
        print()


def main() -> None:
    print("[1/4] Loading configuration...")
    load_env(ENV_PATH)

    query = get_user_query()
    api_key = required_env("PINECONE_API_KEY")
    index_name = required_env("PINECONE_INDEX_NAME")
    namespace = env_value("PINECONE_NAMESPACE", DEFAULT_NAMESPACE)
    ollama_host = env_value("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)
    ollama_model = env_value("OLLAMA_EMBED_MODEL", DEFAULT_OLLAMA_EMBED_MODEL)
    expected_dimension = int_env(
        "PINECONE_EXPECTED_DIMENSION", DEFAULT_EXPECTED_DIMENSION
    )
    top_k = int_env("PINECONE_TOP_K", DEFAULT_TOP_K)

    print(f"[2/4] Embedding query with Ollama model {ollama_model!r}...")
    query_vector = embed_query(query, ollama_host, ollama_model, expected_dimension)
    print(f"      Query embedding dimensions: {len(query_vector)}")

    print(f"[3/4] Searching Pinecone index {index_name!r}...")
    response = query_pinecone(api_key, index_name, namespace, query_vector, top_k)

    print(f"[4/4] Search complete.")
    print()
    print_matches(response_matches(response), top_k)


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, RuntimeError) as exc:
        raise SystemExit(f"Error: {exc}") from exc
