from answer_with_context import (
    DEFAULT_CHAT_BASE_URL,
    DEFAULT_CHAT_MODEL,
    DEFAULT_CHAT_PATH,
    DEFAULT_EXPECTED_DIMENSION,
    DEFAULT_NAMESPACE,
    DEFAULT_NUM_PREDICT,
    DEFAULT_OLLAMA_EMBED_MODEL,
    DEFAULT_OLLAMA_HOST,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_K,
    ENV_PATH,
    call_gpt_oss,
    embed_query,
    env_value,
    float_env,
    int_env,
    load_env,
    normalized_matches,
    query_pinecone,
    required_env,
    response_matches,
)


def grounded_chat(
    query: str,
    index_name: str,
    namespace: str | None = None,
    top_k: int | None = None,
) -> dict[str, object]:
    query = query.strip()
    index_name = index_name.strip()
    namespace = namespace.strip() if namespace else ""

    if not query:
        raise ValueError("Query is required")
    if not index_name:
        raise ValueError("Pinecone index name is required")
    if top_k is not None and top_k <= 0:
        raise ValueError("top_k must be greater than 0")

    load_env(ENV_PATH)

    pinecone_api_key = required_env("PINECONE_API_KEY")
    namespace = namespace or env_value("PINECONE_NAMESPACE", DEFAULT_NAMESPACE)
    ollama_host = env_value("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)
    embed_model = env_value("OLLAMA_EMBED_MODEL", DEFAULT_OLLAMA_EMBED_MODEL)
    expected_dimension = int_env(
        "PINECONE_EXPECTED_DIMENSION",
        DEFAULT_EXPECTED_DIMENSION,
    )
    top_k = top_k or int_env("PINECONE_TOP_K", DEFAULT_TOP_K)
    ollama_api_key = required_env("OLLAMA_API_KEY")
    chat_base_url = env_value("OLLAMA_CHAT_BASE_URL", DEFAULT_CHAT_BASE_URL)
    chat_model = env_value("OLLAMA_CHAT_MODEL", DEFAULT_CHAT_MODEL)
    chat_path = env_value("OLLAMA_CHAT_PATH", DEFAULT_CHAT_PATH)
    temperature = float_env("OLLAMA_ANSWER_TEMPERATURE", DEFAULT_TEMPERATURE)
    num_predict = int_env("OLLAMA_ANSWER_NUM_PREDICT", DEFAULT_NUM_PREDICT)

    query_vector = embed_query(query, ollama_host, embed_model, expected_dimension)
    pinecone_response = query_pinecone(
        pinecone_api_key,
        index_name,
        namespace,
        query_vector,
        top_k,
    )
    chunks = normalized_matches(response_matches(pinecone_response))
    if not chunks:
        raise RuntimeError("Pinecone returned no matching chunks")

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

    return {
        "status": "ok",
        "query": query,
        "answer": answer,
        "index_name": index_name,
        "namespace": namespace,
        "top_k": top_k,
        "chunks": chunks,
    }
