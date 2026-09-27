import os
import sys
import warnings
from pathlib import Path
from typing import Any, TypedDict

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_pinecone import PineconeVectorStore

warnings.filterwarnings(
    "ignore",
    message="The default value of `allowed_objects` will change*",
)

from langgraph.graph import END, START, StateGraph


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"

DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_OLLAMA_EMBED_MODEL = "nomic-embed-text"
DEFAULT_NAMESPACE = "coachx-sample"
DEFAULT_TOP_K = 3
DEFAULT_CHAT_BASE_URL = "https://ollama.com"
DEFAULT_CHAT_MODEL = "gpt-oss:20b-cloud"
DEFAULT_TEMPERATURE = 0.0


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


class RagState(TypedDict, total=False):
    query: str
    index_name: str
    namespace: str
    top_k: int
    ollama_host: str
    embed_model: str
    ollama_api_key: str
    chat_base_url: str
    chat_model: str
    temperature: float
    results: list[tuple[Any, float]]
    answer: str


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value or value.startswith("<"):
        raise RuntimeError(f"{name} is missing or still set to a placeholder")
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
        raise RuntimeError(f"{name} must be an integer") from exc

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
        raise RuntimeError(f"{name} must be a number") from exc


def bearer_token(value: str) -> str:
    stripped = value.strip()
    if stripped.lower().startswith("bearer "):
        return stripped.split(None, 1)[1].strip()
    return stripped


def get_user_query() -> str:
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:]).strip()
    else:
        query = input("Enter your question: ").strip()

    if not query:
        raise RuntimeError("Question cannot be empty")

    return query


def chunk_id(document, fallback: str) -> str:
    document_id = getattr(document, "id", None)
    if document_id:
        return str(document_id)

    metadata = document.metadata or {}
    return str(metadata.get("id") or metadata.get("chunk_id") or fallback)


def build_context(results) -> str:
    parts = []
    for index, (document, score) in enumerate(results, start=1):
        parts.append(
            f"[Chunk {index}]\n"
            f"ID: {chunk_id(document, f'chunk-{index}')}\n"
            f"Score: {score:.4f}\n"
            f"Text: {document.page_content}"
        )

    return "\n\n".join(parts)


def print_sources(results) -> None:
    print("Sources:")
    for index, (document, score) in enumerate(results, start=1):
        print(f"{index}. ID: {chunk_id(document, f'chunk-{index}')}")
        print(f"   Score: {score:.4f}")
        print(f"   Text: {document.page_content}")
        print()


def load_config_node(state: RagState) -> RagState:
    print("[1/4] Loading config...")
    load_dotenv(ENV_PATH)

    required_env("PINECONE_API_KEY")
    return {
        **state,
        "index_name": required_env("PINECONE_INDEX_NAME"),
        "namespace": env_value("PINECONE_NAMESPACE", DEFAULT_NAMESPACE),
        "top_k": int_env("PINECONE_TOP_K", DEFAULT_TOP_K),
        "ollama_host": env_value("OLLAMA_HOST", DEFAULT_OLLAMA_HOST),
        "embed_model": env_value("OLLAMA_EMBED_MODEL", DEFAULT_OLLAMA_EMBED_MODEL),
        "ollama_api_key": required_env("OLLAMA_API_KEY"),
        "chat_base_url": env_value("OLLAMA_CHAT_BASE_URL", DEFAULT_CHAT_BASE_URL),
        "chat_model": env_value("OLLAMA_CHAT_MODEL", DEFAULT_CHAT_MODEL),
        "temperature": float_env("OLLAMA_ANSWER_TEMPERATURE", DEFAULT_TEMPERATURE),
    }


def retrieve_chunks_node(state: RagState) -> RagState:
    print("[2/4] Connecting to Pinecone with LangChain...")
    embeddings = OllamaEmbeddings(
        model=state["embed_model"],
        base_url=state["ollama_host"],
    )
    vector_store = PineconeVectorStore.from_existing_index(
        index_name=state["index_name"],
        embedding=embeddings,
        text_key="text",
        namespace=state["namespace"],
    )

    print(f"[3/4] Retrieving top {state['top_k']} chunks...")
    results = vector_store.similarity_search_with_score(
        state["query"],
        k=state["top_k"],
    )
    if not results:
        raise RuntimeError("No matching chunks were found")

    return {**state, "results": results}


def generate_answer_node(state: RagState) -> RagState:
    print("[4/4] Asking GPT-OSS...")
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Answer using only the retrieved chunks. If the chunks do not "
                "contain enough information, say that clearly. Keep the answer "
                "concise and mention the chunk IDs you used.",
            ),
            (
                "human",
                "Question:\n{question}\n\n"
                "Retrieved chunks:\n{context}\n\n"
                "Provide a grounded answer based only on these chunks.",
            ),
        ]
    )
    llm = ChatOllama(
        model=state["chat_model"],
        base_url=state["chat_base_url"],
        temperature=state["temperature"],
        client_kwargs={
            "headers": {
                "Authorization": f"Bearer {bearer_token(state['ollama_api_key'])}",
            }
        },
    )
    messages = prompt.format_messages(
        question=state["query"],
        context=build_context(state["results"]),
    )
    answer = llm.invoke(messages)

    return {**state, "answer": answer.content}


def build_graph():
    graph = StateGraph(RagState)

    graph.add_node("load_config", load_config_node)
    graph.add_node("retrieve_chunks", retrieve_chunks_node)
    graph.add_node("generate_answer", generate_answer_node)

    graph.add_edge(START, "load_config")
    graph.add_edge("load_config", "retrieve_chunks")
    graph.add_edge("retrieve_chunks", "generate_answer")
    graph.add_edge("generate_answer", END)

    return graph.compile()


def main() -> None:
    query = get_user_query()
    rag_graph = build_graph()
    final_state = rag_graph.invoke({"query": query})

    print()
    print("Answer:")
    print(final_state["answer"])
    print()
    print_sources(final_state["results"])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(f"Error: {exc}") from exc
