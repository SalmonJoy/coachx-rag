import json
import os
from pathlib import Path
from typing import Any

from pinecone import Pinecone


ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"

DEFAULT_EMBEDDINGS_JSONL_PATH = "source/chunks/RAG demo embeddings.jsonl"
DEFAULT_NAMESPACE = "coachx-sample"
DEFAULT_BATCH_SIZE = 100
DEFAULT_EXPECTED_DIMENSION = 768


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


def resolve_path(raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = ROOT / path
    return path


def namespace_from_env() -> str:
    raw = os.environ.get("PINECONE_NAMESPACE", DEFAULT_NAMESPACE)
    if raw.strip().startswith("<"):
        return DEFAULT_NAMESPACE

    return raw.strip()


def embeddings_path_from_env() -> Path:
    return resolve_path(
        env_value("PINECONE_EMBEDDINGS_JSONL_PATH", DEFAULT_EMBEDDINGS_JSONL_PATH)
    )


def numeric_values(record: dict[str, Any], line_number: int) -> list[float]:
    values = record.get("values")
    if not isinstance(values, list):
        raise RuntimeError(f"Line {line_number} has missing or non-list values")

    numeric: list[float] = []
    for index, value in enumerate(values):
        if not isinstance(value, (int, float)):
            raise RuntimeError(
                f"Line {line_number} values[{index}] is not numeric: {value!r}"
            )
        numeric.append(float(value))

    return numeric


def metadata_from_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "text": record.get("text", ""),
        "source_file": record.get("source_file", ""),
        "heading": record.get("heading", ""),
        "heading_level": record.get("heading_level", ""),
        "start_line": record.get("start_line", ""),
        "end_line": record.get("end_line", ""),
        "embedding_model": record.get("embedding_model", ""),
    }


def load_vectors(jsonl_path: Path, expected_dimension: int) -> list[dict[str, Any]]:
    if not jsonl_path.exists():
        raise FileNotFoundError(f"Missing embeddings JSONL file: {jsonl_path}")

    vectors: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    with jsonl_path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Invalid JSON on line {line_number}: {exc}") from exc

            chunk_id = str(record.get("chunk_id", "")).strip()
            text = str(record.get("text", "")).strip()
            if not chunk_id:
                raise RuntimeError(f"Line {line_number} is missing chunk_id")
            if chunk_id in seen_ids:
                raise RuntimeError(f"Duplicate chunk_id found: {chunk_id}")
            if not text:
                raise RuntimeError(f"Line {line_number} / {chunk_id} has empty text")

            values = numeric_values(record, line_number)
            if len(values) != expected_dimension:
                raise RuntimeError(
                    f"Line {line_number} / {chunk_id} has {len(values)} dimensions, "
                    f"expected {expected_dimension}"
                )

            seen_ids.add(chunk_id)
            vectors.append(
                {
                    "id": chunk_id,
                    "values": values,
                    "metadata": metadata_from_record(record),
                }
            )

    if not vectors:
        raise RuntimeError(f"No vectors found in {jsonl_path}")

    return vectors


def batched(items: list[dict[str, Any]], batch_size: int) -> list[list[dict[str, Any]]]:
    return [items[index : index + batch_size] for index in range(0, len(items), batch_size)]


def get_index_client(client: Pinecone, index_name: str) -> Any:
    if hasattr(client, "index"):
        return client.index(index_name)

    return client.Index(index_name)


def main() -> None:
    load_env(ENV_PATH)

    api_key = required_env("PINECONE_API_KEY")
    index_name = required_env("PINECONE_INDEX_NAME")
    namespace = namespace_from_env()
    jsonl_path = embeddings_path_from_env()
    batch_size = int_env("PINECONE_BATCH_SIZE", DEFAULT_BATCH_SIZE)
    expected_dimension = int_env(
        "PINECONE_EXPECTED_DIMENSION", DEFAULT_EXPECTED_DIMENSION
    )

    print(f"[1/3] Loading vectors from {jsonl_path}...")
    vectors = load_vectors(jsonl_path, expected_dimension)

    print(f"[2/3] Upserting {len(vectors)} vectors to Pinecone index {index_name!r}...")
    client = Pinecone(api_key=api_key)
    index = get_index_client(client, index_name)

    uploaded = 0
    for batch in batched(vectors, batch_size):
        response = index.upsert(vectors=batch, namespace=namespace)
        uploaded += getattr(response, "upserted_count", len(batch))

    print(f"[3/3] Uploaded {uploaded} vectors to namespace {namespace!r}.")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, RuntimeError) as exc:
        raise SystemExit(f"Error: {exc}") from exc
