from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from pinecone import Pinecone

from chunk_md_to_jsonl import chunk_markdown, write_jsonl
from convert_pdf_to_md import convert_pdf_to_markdown
from ollama_embed_texts import (
    DEFAULT_OLLAMA_EMBED_MODEL,
    DEFAULT_OLLAMA_HOST,
    embed_chunks,
    env_value,
    load_env as load_optional_env,
    write_embeddings_jsonl,
)
from upload_to_pinecone import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_EXPECTED_DIMENSION,
    ENV_PATH,
    batched,
    get_index_client,
    int_env,
    load_env,
    load_vectors,
    namespace_from_env,
    required_env,
)


ROOT = Path(__file__).resolve().parents[3]
RUNS_DIR = ROOT / "backend" / "data" / "runs"


async def ingest_pdf_upload(
    file: UploadFile,
    index_name: str,
    namespace: str | None,
) -> dict[str, object]:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise ValueError("Only PDF uploads are supported")

    index_name = index_name.strip()
    if not index_name:
        raise ValueError("Pinecone index name is required")

    namespace = namespace.strip() if namespace else ""

    run_id = uuid4().hex
    run_dir = RUNS_DIR / run_id
    input_path = run_dir / "input.pdf"
    markdown_path = run_dir / "output.md"
    chunks_path = run_dir / "chunks.jsonl"
    embeddings_path = run_dir / "embeddings.jsonl"

    run_dir.mkdir(parents=True, exist_ok=True)
    input_path.write_bytes(await file.read())

    convert_pdf_to_markdown(input_path, markdown_path)

    chunks = chunk_markdown(markdown_path)
    write_jsonl(chunks, chunks_path)

    load_optional_env(ENV_PATH)
    ollama_host = env_value("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)
    embed_model = env_value("OLLAMA_EMBED_MODEL", DEFAULT_OLLAMA_EMBED_MODEL)
    embeddings = embed_chunks(chunks, ollama_host, embed_model)
    write_embeddings_jsonl(chunks, embeddings, embeddings_path, embed_model)

    load_env(ENV_PATH)
    api_key = required_env("PINECONE_API_KEY")
    namespace = namespace or namespace_from_env()
    batch_size = int_env("PINECONE_BATCH_SIZE", DEFAULT_BATCH_SIZE)
    expected_dimension = int_env(
        "PINECONE_EXPECTED_DIMENSION",
        DEFAULT_EXPECTED_DIMENSION,
    )

    vectors = load_vectors(embeddings_path, expected_dimension)
    client = Pinecone(api_key=api_key)
    index = get_index_client(client, index_name)

    uploaded = 0
    for batch in batched(vectors, batch_size):
        response = index.upsert(vectors=batch, namespace=namespace)
        uploaded += getattr(response, "upserted_count", len(batch))

    return {
        "status": "ok",
        "run_id": run_id,
        "uploaded_vectors": uploaded,
        "markdown_path": markdown_path.relative_to(ROOT).as_posix(),
        "chunks_path": chunks_path.relative_to(ROOT).as_posix(),
        "embeddings_path": embeddings_path.relative_to(ROOT).as_posix(),
        "pinecone_index": index_name,
        "pinecone_namespace": namespace,
    }
