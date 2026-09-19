import csv
import os
from pathlib import Path
from typing import Any

from pinecone import Pinecone


ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"

DEFAULT_CSV_PATH = "nomic_embeddings.csv"
DEFAULT_NAMESPACE = "coachx-sample"
DEFAULT_BATCH_SIZE = 100
DEFAULT_EXPECTED_DIMENSION = 768
EMBEDDING_MODEL = "nomic-embed-text"


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


def csv_path_from_env() -> Path:
    raw = os.environ.get("PINECONE_CSV_PATH", DEFAULT_CSV_PATH).strip()
    if not raw or raw.startswith("<"):
        raw = DEFAULT_CSV_PATH

    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path

    return path


def namespace_from_env() -> str:
    raw = os.environ.get("PINECONE_NAMESPACE", DEFAULT_NAMESPACE)
    if raw.strip().startswith("<"):
        return DEFAULT_NAMESPACE

    return raw.strip()


def dimension_columns(fieldnames: list[str] | None) -> list[str]:
    if not fieldnames:
        raise RuntimeError("CSV is missing a header row")

    columns = [name for name in fieldnames if name.startswith("dim_")]
    if not columns:
        raise RuntimeError("CSV does not contain any dim_* vector columns")

    return sorted(columns, key=lambda name: int(name.removeprefix("dim_")))


def load_vectors(csv_path: Path, expected_dimension: int) -> list[dict[str, Any]]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing CSV file: {csv_path}")

    vectors: list[dict[str, Any]] = []
    with csv_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        dims = dimension_columns(reader.fieldnames)

        if len(dims) != expected_dimension:
            raise RuntimeError(
                f"Expected {expected_dimension} dimension columns, found {len(dims)}"
            )

        for row_number, row in enumerate(reader, start=1):
            try:
                values = [float(row[column]) for column in dims]
            except (TypeError, ValueError) as exc:
                raise RuntimeError(
                    f"Row {row_number} has a non-numeric vector value"
                ) from exc

            if len(values) != expected_dimension:
                raise RuntimeError(
                    f"Row {row_number} has {len(values)} values, "
                    f"expected {expected_dimension}"
                )

            row_id = row.get("id", str(row_number)).strip() or str(row_number)
            text = row.get("text", "").strip()

            vectors.append(
                {
                    "id": f"sample-text-{row_id}",
                    "values": values,
                    "metadata": {
                        "text": text,
                        "source": csv_path.name,
                        "row_id": int(row_id) if row_id.isdigit() else row_id,
                        "embedding_model": EMBEDDING_MODEL,
                    },
                }
            )

    if not vectors:
        raise RuntimeError(f"No vectors found in {csv_path}")

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
    csv_path = csv_path_from_env()
    batch_size = int_env("PINECONE_BATCH_SIZE", DEFAULT_BATCH_SIZE)
    expected_dimension = int_env(
        "PINECONE_EXPECTED_DIMENSION", DEFAULT_EXPECTED_DIMENSION
    )

    vectors = load_vectors(csv_path, expected_dimension)

    client = Pinecone(api_key=api_key)
    index = get_index_client(client, index_name)

    uploaded = 0
    for batch in batched(vectors, batch_size):
        response = index.upsert(vectors=batch, namespace=namespace)
        uploaded += getattr(response, "upserted_count", len(batch))

    print(
        f"Uploaded {uploaded} vectors to Pinecone index "
        f"{index_name!r} namespace {namespace!r}"
    )


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, RuntimeError) as exc:
        raise SystemExit(f"Error: {exc}") from exc
