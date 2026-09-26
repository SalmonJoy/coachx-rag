from typing import Any

from pinecone import Pinecone

from upload_to_pinecone import ENV_PATH, get_index_client, load_env, required_env


DEFAULT_CHUNK_LIMIT = 100
MAX_CHUNK_LIMIT = 1000


def pinecone_client() -> Pinecone:
    load_env(ENV_PATH)
    return Pinecone(api_key=required_env("PINECONE_API_KEY"))


def object_value(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(key, default)

    return getattr(item, key, default)


def response_dict(response: Any) -> dict[str, Any]:
    if hasattr(response, "to_dict"):
        return response.to_dict()

    if isinstance(response, dict):
        return response

    return {}


def list_index_names() -> list[str]:
    client = pinecone_client()
    indexes = client.list_indexes()

    if hasattr(indexes, "names"):
        return sorted(str(name) for name in indexes.names())

    names = []
    for index in indexes:
        name = object_value(index, "name")
        if name:
            names.append(str(name))

    return sorted(names)


def list_namespaces(index_name: str) -> list[dict[str, Any]]:
    index_name = index_name.strip()
    if not index_name:
        raise ValueError("Pinecone index name is required")

    client = pinecone_client()
    index = get_index_client(client, index_name)
    stats = response_dict(index.describe_index_stats())
    namespaces = stats.get("namespaces") or {}

    results = []
    for name, details in namespaces.items():
        results.append(
            {
                "name": str(name),
                "vector_count": int(object_value(details, "vector_count", 0) or 0),
            }
        )

    return sorted(results, key=lambda item: item["name"])


def listed_ids(page: Any) -> list[str]:
    vectors = object_value(page, "vectors", [])
    ids = []
    for item in vectors or []:
        vector_id = object_value(item, "id")
        if vector_id:
            ids.append(str(vector_id))

    return ids


def vector_metadata(vector: Any) -> dict[str, Any]:
    metadata = object_value(vector, "metadata", {}) or {}
    return metadata if isinstance(metadata, dict) else {}


def fetched_vectors(response: Any) -> dict[str, Any]:
    data = response_dict(response)
    vectors = data.get("vectors") or {}
    return vectors if isinstance(vectors, dict) else {}


def chunk_from_vector(vector_id: str, vector: Any) -> dict[str, Any]:
    metadata = vector_metadata(vector)
    return {
        "id": vector_id,
        "text": str(metadata.get("text", "")),
        "heading": str(metadata.get("heading", "")),
        "source_file": str(metadata.get("source_file", "")),
        "start_line": metadata.get("start_line", ""),
        "end_line": metadata.get("end_line", ""),
        "embedding_model": str(metadata.get("embedding_model", "")),
    }


def list_chunks(index_name: str, namespace: str, limit: int = DEFAULT_CHUNK_LIMIT) -> list[dict[str, Any]]:
    index_name = index_name.strip()
    namespace = namespace.strip()

    if not index_name:
        raise ValueError("Pinecone index name is required")
    if not namespace:
        raise ValueError("Pinecone namespace is required")
    if limit <= 0 or limit > MAX_CHUNK_LIMIT:
        raise ValueError(f"Limit must be between 1 and {MAX_CHUNK_LIMIT}")

    client = pinecone_client()
    index = get_index_client(client, index_name)

    ids: list[str] = []
    for page in index.list(namespace=namespace, limit=min(limit, DEFAULT_CHUNK_LIMIT)):
        ids.extend(listed_ids(page))
        if len(ids) >= limit:
            ids = ids[:limit]
            break

    if not ids:
        return []

    chunks_by_id: dict[str, dict[str, Any]] = {}
    for offset in range(0, len(ids), DEFAULT_CHUNK_LIMIT):
        batch_ids = ids[offset : offset + DEFAULT_CHUNK_LIMIT]
        fetched = fetched_vectors(index.fetch(ids=batch_ids, namespace=namespace))
        for vector_id in batch_ids:
            vector = fetched.get(vector_id)
            if vector:
                chunks_by_id[vector_id] = chunk_from_vector(vector_id, vector)

    return [chunks_by_id[vector_id] for vector_id in ids if vector_id in chunks_by_id]
