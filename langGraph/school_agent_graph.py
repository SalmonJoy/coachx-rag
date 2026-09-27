import json
import os
import sys
import warnings
from pathlib import Path
from typing import Any, TypedDict

from dotenv import load_dotenv
from langchain_ollama import ChatOllama

warnings.filterwarnings(
    "ignore",
    message="The default value of `allowed_objects` will change*",
)

from langgraph.graph import END, START, StateGraph

from api_call_tool import call_external_api
from google_sheet_fetch_tool import fetch_google_sheet_data
from sql_data_tool import fetch_sql_data
from vector_db_search_tool import search_vector_db


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"

DEFAULT_CHAT_BASE_URL = "https://ollama.com"
DEFAULT_ROUTER_MODEL = "gpt-oss:20b-cloud"
DEFAULT_FINAL_MODEL = "gpt-oss:120b-cloud"
DEFAULT_TEMPERATURE = 0.0

TOOL_REGISTRY = {
    "fetch_sql_data": {
        "tool": fetch_sql_data,
        "argument_name": "query",
        "description": "Use for structured grade, student, subject, or teacher rows.",
    },
    "call_external_api": {
        "tool": call_external_api,
        "argument_name": "endpoint",
        "description": "Use for student profiles, teacher schedules, or subject summaries.",
    },
    "search_vector_db": {
        "tool": search_vector_db,
        "argument_name": "search_query",
        "description": "Use for semantic subject-note searches and learning support hints.",
    },
    "fetch_google_sheet_data": {
        "tool": fetch_google_sheet_data,
        "argument_name": "sheet_name",
        "description": "Use for spreadsheet-like attendance, assignments, or grades rows.",
    },
}


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


class AgentState(TypedDict, total=False):
    query: str
    ollama_api_key: str
    chat_base_url: str
    router_model: str
    final_model: str
    temperature: float
    selected_tools: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
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
        query = input("Enter your school question: ").strip()

    if not query:
        raise RuntimeError("Question cannot be empty")

    return query


def make_llm(model: str, state: AgentState) -> ChatOllama:
    return ChatOllama(
        model=model,
        base_url=state["chat_base_url"],
        temperature=state["temperature"],
        client_kwargs={
            "headers": {
                "Authorization": f"Bearer {bearer_token(state['ollama_api_key'])}",
            }
        },
    )


def fallback_tool_plan(query: str) -> list[dict[str, Any]]:
    return [
        {
            "tool_name": "search_vector_db",
            "arguments": {"search_query": query},
            "reason": "Fallback semantic search because the router response was invalid.",
        }
    ]


def extract_json_payload(text: str) -> Any:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    list_start = cleaned.find("[")
    list_end = cleaned.rfind("]")
    if list_start != -1 and list_end != -1 and list_end > list_start:
        return json.loads(cleaned[list_start : list_end + 1])

    object_start = cleaned.find("{")
    object_end = cleaned.rfind("}")
    if object_start != -1 and object_end != -1 and object_end > object_start:
        return json.loads(cleaned[object_start : object_end + 1])

    raise ValueError("Could not parse JSON from router response")


def normalize_tool_plan(payload: Any, query: str) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        payload = payload.get("tools") or payload.get("selected_tools") or [payload]

    if not isinstance(payload, list):
        return fallback_tool_plan(query)

    selected_tools = []
    for item in payload:
        if not isinstance(item, dict):
            continue

        tool_name = item.get("tool_name") or item.get("name") or item.get("tool")
        if tool_name not in TOOL_REGISTRY:
            continue

        arguments = item.get("arguments") or item.get("args") or {}
        if not isinstance(arguments, dict):
            arguments = {}

        argument_name = TOOL_REGISTRY[tool_name]["argument_name"]
        if not str(arguments.get(argument_name, "")).strip():
            arguments[argument_name] = query

        selected_tools.append(
            {
                "tool_name": tool_name,
                "arguments": arguments,
                "reason": item.get("reason", "Selected by GPT-OSS 20B router."),
            }
        )

    return selected_tools or fallback_tool_plan(query)


def load_config_node(state: AgentState) -> AgentState:
    print("[1/4] Loading config...")
    load_dotenv(ENV_PATH)

    return {
        **state,
        "ollama_api_key": required_env("OLLAMA_API_KEY"),
        "chat_base_url": env_value("OLLAMA_CHAT_BASE_URL", DEFAULT_CHAT_BASE_URL),
        "router_model": env_value("OLLAMA_ROUTER_MODEL", DEFAULT_ROUTER_MODEL),
        "final_model": env_value("OLLAMA_FINAL_MODEL", DEFAULT_FINAL_MODEL),
        "temperature": float_env("OLLAMA_ANSWER_TEMPERATURE", DEFAULT_TEMPERATURE),
    }


def plan_tools_node(state: AgentState) -> AgentState:
    print("[2/4] Asking GPT-OSS 20B which tools to use...")
    tool_descriptions = "\n".join(
        f"- {name}: {details['description']} Required argument: {details['argument_name']}."
        for name, details in TOOL_REGISTRY.items()
    )
    router_prompt = (
        "You are a tool router for a school-data LangGraph demo.\n"
        "Choose one or more tools that can answer the user question.\n"
        "Return only valid JSON as an array. No markdown, no commentary.\n"
        "Each array item must have tool_name, arguments, and reason.\n\n"
        "Routing guidance:\n"
        "- Use search_vector_db for learning needs, academic support, concepts, or what students are studying.\n"
        "- Use fetch_sql_data for grades, joined student-subject-teacher rows, or score comparisons.\n"
        "- Use fetch_google_sheet_data for attendance, assignments, or spreadsheet-style grade rows.\n"
        "- Use call_external_api for student profiles, teacher schedules, or subject summaries.\n"
        "- Select multiple tools when the question needs more than one kind of data.\n\n"
        "Example: for 'Which students may need extra help in algebra?', include "
        "search_vector_db with the full question, and optionally fetch_sql_data for grades.\n\n"
        f"Available tools:\n{tool_descriptions}\n\n"
        f"User question: {state['query']}\n"
    )

    llm = make_llm(state["router_model"], state)
    response = llm.invoke(router_prompt)

    try:
        selected_tools = normalize_tool_plan(
            extract_json_payload(str(response.content)),
            state["query"],
        )
    except Exception:
        selected_tools = fallback_tool_plan(state["query"])

    return {**state, "selected_tools": selected_tools}


def run_tools_node(state: AgentState) -> AgentState:
    print("[3/4] Running selected tools...")
    tool_results = []

    for selected_tool in state["selected_tools"]:
        tool_name = selected_tool["tool_name"]
        arguments = selected_tool["arguments"]
        tool = TOOL_REGISTRY[tool_name]["tool"]
        result = tool.invoke(arguments)
        tool_results.append(
            {
                "tool_name": tool_name,
                "arguments": arguments,
                "reason": selected_tool.get("reason", ""),
                "result": result,
            }
        )

    return {**state, "tool_results": tool_results}


def generate_answer_node(state: AgentState) -> AgentState:
    print("[4/4] Asking GPT-OSS 120B to generate the final answer...")
    tool_data = json.dumps(state["tool_results"], indent=2, ensure_ascii=False)
    final_prompt = (
        "You are a helpful school assistant.\n"
        "Answer the user using only the tool results below.\n"
        "If the fetched data is not enough, say what is missing.\n"
        "Mention which tool results you used.\n\n"
        f"User question:\n{state['query']}\n\n"
        f"Fetched tool data:\n{tool_data}\n\n"
        "Final grounded answer:"
    )

    llm = make_llm(state["final_model"], state)
    response = llm.invoke(final_prompt)

    return {**state, "answer": str(response.content).strip()}


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("load_config", load_config_node)
    graph.add_node("plan_tools", plan_tools_node)
    graph.add_node("run_tools", run_tools_node)
    graph.add_node("generate_answer", generate_answer_node)

    graph.add_edge(START, "load_config")
    graph.add_edge("load_config", "plan_tools")
    graph.add_edge("plan_tools", "run_tools")
    graph.add_edge("run_tools", "generate_answer")
    graph.add_edge("generate_answer", END)

    return graph.compile()


def print_selected_tools(selected_tools: list[dict[str, Any]]) -> None:
    print()
    print("Selected tools:")
    for selected_tool in selected_tools:
        print(
            f"- {selected_tool['tool_name']}: "
            f"{json.dumps(selected_tool['arguments'], ensure_ascii=False)}"
        )
        if selected_tool.get("reason"):
            print(f"  Reason: {selected_tool['reason']}")


def print_tool_results(tool_results: list[dict[str, Any]]) -> None:
    print()
    print("Tool result summary:")
    for index, item in enumerate(tool_results, start=1):
        result = item["result"]
        print(f"{index}. {item['tool_name']}")
        if "rows" in result:
            print(f"   Rows: {len(result['rows'])}")
        elif "matches" in result:
            print(f"   Matches: {len(result['matches'])}")
        elif "data" in result:
            print(f"   Payload keys: {', '.join(result['data'].keys())}")


def main() -> None:
    query = get_user_query()
    graph = build_graph()
    final_state = graph.invoke({"query": query})

    print_selected_tools(final_state["selected_tools"])
    print_tool_results(final_state["tool_results"])
    print()
    print("Answer:")
    print(final_state["answer"])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(f"Error: {exc}") from exc
