import json
import os
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"

DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_OLLAMA_EMBED_MODEL = "nomic-embed-text"
DEFAULT_CHUNKS_JSONL_PATH = "source/chunks/RAG demo.jsonl"
DEFAULT_EMBEDDINGS_JSONL_PATH = "source/chunks/RAG demo embeddings.jsonl"

METADATA_COLUMNS = [
    "chunk_id",
    "source_file",
    "heading",
    "heading_level",
    "start_line",
    "end_line",
    "text",
]


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


def env_value(name: str, default: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value or value.startswith("<"):
        return default
    return value


def resolve_path(raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = ROOT / path
    return path


def load_chunks(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Chunks JSONL file not found: {path}")

    chunks: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                chunk = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Invalid JSON on line {line_number}: {exc}") from exc

            chunk_id = str(chunk.get("chunk_id", "")).strip()
            text = str(chunk.get("text", "")).strip()
            if not chunk_id:
                raise RuntimeError(f"Line {line_number} is missing chunk_id")
            if not text:
                raise RuntimeError(f"Line {line_number} / {chunk_id} has empty text")

            chunks.append(chunk)

    if not chunks:
        raise RuntimeError(f"No chunks found in {path}")

    return chunks


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


def embed_chunks(
    chunks: list[dict[str, Any]],
    ollama_host: str,
    model: str,
) -> list[list[float]]:
    url = f"{ollama_host.rstrip('/')}/api/embed"
    texts = [str(chunk["text"]).strip() for chunk in chunks]
    body = {
        "model": model,
        "input": texts,
        "truncate": True,
    }

    try:
        response = requests.post(url, json=body, timeout=120)
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

    if len(embeddings) != len(chunks):
        raise RuntimeError(
            f"Ollama returned {len(embeddings)} embeddings for {len(chunks)} chunks"
        )

    dimensions = {len(embedding) for embedding in embeddings}
    if len(dimensions) != 1:
        raise RuntimeError(f"Embeddings have inconsistent dimensions: {dimensions}")

    return embeddings


def write_embeddings_jsonl(
    chunks: list[dict[str, Any]],
    embeddings: list[list[float]],
    output_path: Path,
    model: str,
) -> None:
    if not embeddings:
        raise RuntimeError("No embeddings to write")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    dimensions = len(embeddings[0])

    with output_path.open("w", encoding="utf-8", newline="\n") as file:
        for chunk, embedding in zip(chunks, embeddings):
            record = {column: chunk.get(column, "") for column in METADATA_COLUMNS}
            record["embedding_model"] = model
            record["embedding_dimensions"] = dimensions
            record["values"] = embedding
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    load_env(ENV_PATH)

    input_path = resolve_path(
        env_value("OLLAMA_CHUNKS_JSONL_PATH", DEFAULT_CHUNKS_JSONL_PATH)
    )
    output_path = resolve_path(
        env_value("OLLAMA_CHUNKS_EMBEDDINGS_JSONL_PATH", DEFAULT_EMBEDDINGS_JSONL_PATH)
    )
    ollama_host = env_value("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)
    model = env_value("OLLAMA_EMBED_MODEL", DEFAULT_OLLAMA_EMBED_MODEL)

    print(f"[1/4] Loading chunks from {input_path}...")
    chunks = load_chunks(input_path)

    print(f"[2/4] Embedding {len(chunks)} chunks with {model}...")
    embeddings = embed_chunks(chunks, ollama_host, model)

    print(f"[3/4] Writing JSONL: {output_path}...")
    write_embeddings_jsonl(chunks, embeddings, output_path, model)

    print(
        f"[4/4] Done. Wrote {len(embeddings)} embeddings "
        f"with {len(embeddings[0])} dimensions."
    )


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, RuntimeError) as exc:
        raise SystemExit(f"Error: {exc}") from exc
