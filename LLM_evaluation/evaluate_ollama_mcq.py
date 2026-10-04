import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"

DEFAULT_DATASET_PATH = ROOT / "LLM_evaluation" / "financial_services_mcq_eval.jsonl"
DEFAULT_RESULTS_PATH = ROOT / "LLM_evaluation" / "ollama_eval_results.jsonl"
DEFAULT_BASE_URL = "https://ollama.com"
DEFAULT_CHAT_PATH = "/api/chat"
DEFAULT_NUM_PREDICT = 128
MIN_NUM_PREDICT = 64
DEFAULT_TEMPERATURE = 0

DEFAULT_MODELS = [
    "llama4:scout-cloud",
    "llama4:maverick-cloud",
    "llama3.3:70b-cloud",
    "qwen3:480b-cloud",
    "qwen3-coder:480b-cloud",
    "qwen3-vl:235b-cloud",
    "gpt-oss:20b-cloud",
    "gpt-oss:120b-cloud",
]


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


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


def bearer_token(value: str) -> str:
    stripped = value.strip()
    if stripped.lower().startswith("bearer "):
        return stripped.split(None, 1)[1].strip()
    return stripped


def configured_models() -> list[str]:
    raw = os.environ.get("OLLAMA_CHAT_MODELS", "")
    models = [model.strip() for model in raw.split(",") if model.strip()]
    return models or DEFAULT_MODELS


def resolve_path(value: str, default: Path) -> Path:
    if not value or value.startswith("<"):
        return default

    path = Path(value)
    if path.is_absolute():
        return path

    return ROOT / path


def load_questions(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise RuntimeError(f"Dataset file does not exist: {path}")

    questions: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Invalid JSON on line {line_number}: {exc}") from exc

            validate_question(row, line_number)
            questions.append(row)

    if not questions:
        raise RuntimeError(f"No questions found in dataset: {path}")

    return questions


def validate_question(row: dict[str, Any], line_number: int) -> None:
    required_fields = ["id", "topic", "question", "options", "answer"]
    missing = [field for field in required_fields if field not in row]
    if missing:
        raise RuntimeError(f"Line {line_number} is missing fields: {', '.join(missing)}")

    options = row["options"]
    if not isinstance(options, dict) or len(options) < 4:
        raise RuntimeError(f"Line {line_number} must contain at least 4 options")

    answer = str(row["answer"]).strip()
    if answer not in options:
        raise RuntimeError(
            f"Line {line_number} answer {answer!r} is not one of the option keys"
        )


def select_model(models: list[str]) -> str:
    print("Available Ollama Cloud models:")
    for index, model in enumerate(models, start=1):
        print(f"{index}. {model}")

    while True:
        selected = input("Select a model by number: ").strip()
        try:
            selected_index = int(selected)
        except ValueError:
            print("Please enter a valid number.")
            continue

        if 1 <= selected_index <= len(models):
            return models[selected_index - 1]

        print(f"Please choose a number from 1 to {len(models)}.")


def chat_response_content(payload: dict[str, Any]) -> str:
    if isinstance(payload.get("message"), dict):
        return str(payload["message"].get("content", "")).strip()

    if isinstance(payload.get("choices"), list) and payload["choices"]:
        message = payload["choices"][0].get("message", {})
        return str(message.get("content", "")).strip()

    return ""


def format_options(options: dict[str, str]) -> str:
    return "\n".join(f"{key}. {value}" for key, value in options.items())


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


def extract_answer(raw_response: str) -> str | None:
    normalized = raw_response.strip().upper()
    if normalized in {"A", "B", "C", "D"}:
        return normalized

    match = re.search(r"\b([ABCD])\b", normalized)
    if match:
        return match.group(1)

    return None


def check_model_available(
    model: str,
    api_key: str,
    base_url: str,
    chat_path: str,
    num_predict: int,
) -> tuple[bool, str]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearer_token(api_key)}",
    }
    url = f"{base_url.rstrip('/')}/{chat_path.lstrip('/')}"
    body = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "Reply with exactly: A",
            }
        ],
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": num_predict,
        },
    }

    try:
        response = requests.post(url, json=body, headers=headers, timeout=45)
    except requests.RequestException as exc:
        return False, f"connection failed: {exc}"

    if response.status_code != 200:
        return False, f"HTTP {response.status_code}: {short_error(response)}"

    content = chat_response_content(response.json())
    if not content:
        return False, "empty chat response"

    return True, "ok"


def available_models(
    models: list[str],
    api_key: str,
    base_url: str,
    chat_path: str,
    num_predict: int,
) -> list[str]:
    print("Checking model availability...")
    available = []
    for model in models:
        is_available, message = check_model_available(
            model,
            api_key,
            base_url,
            chat_path,
            num_predict,
        )
        if is_available:
            available.append(model)
            print(f"- {model}: available")
        else:
            print(f"- {model}: unavailable ({message})")

    if not available:
        raise RuntimeError("No configured Ollama Cloud models are available")

    print()
    return available


def call_ollama_mcq(
    question: dict[str, Any],
    model: str,
    api_key: str,
    base_url: str,
    chat_path: str,
    num_predict: int,
) -> tuple[str | None, str]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearer_token(api_key)}",
    }
    url = f"{base_url.rstrip('/')}/{chat_path.lstrip('/')}"
    body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are answering multiple-choice evaluation questions. "
                    "Reply with only one letter: A, B, C, or D. Do not explain."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Topic: {question['topic']}\n"
                    f"Question: {question['question']}\n\n"
                    f"Options:\n{format_options(question['options'])}\n\n"
                    "Answer with only A, B, C, or D."
                ),
            },
        ],
        "stream": False,
        "options": {
            "temperature": DEFAULT_TEMPERATURE,
            "num_predict": num_predict,
        },
    }

    try:
        response = requests.post(url, json=body, headers=headers, timeout=120)
    except requests.RequestException as exc:
        raise RuntimeError(f"Request failed: {exc}") from exc

    if response.status_code != 200:
        raise RuntimeError(
            f"Ollama returned HTTP {response.status_code}: {short_error(response)}"
        )

    raw_response = chat_response_content(response.json())

    return extract_answer(raw_response), raw_response


def result_row(
    question: dict[str, Any],
    model: str,
    model_answer: str | None,
    raw_response: str,
    error: str | None = None,
) -> dict[str, Any]:
    expected_answer = str(question["answer"]).strip()
    row = {
        "id": question["id"],
        "topic": question["topic"],
        "model": model,
        "expected_answer": expected_answer,
        "model_answer": model_answer,
        "is_correct": model_answer == expected_answer,
        "raw_response": raw_response,
    }
    if error:
        row["error"] = error

    return row


def write_results(path: Path, results: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        for row in results:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def print_summary(model: str, results: list[dict[str, Any]]) -> None:
    total = len(results)
    correct = sum(1 for row in results if row["is_correct"])
    accuracy = (correct / total) * 100 if total else 0

    print()
    print("Evaluation summary")
    print(f"Model: {model}")
    print(f"Total questions: {total}")
    print(f"Correct: {correct}")
    print(f"Accuracy: {accuracy:.2f}%")
    print()
    print("Per-topic accuracy:")

    topic_totals = Counter(row["topic"] for row in results)
    topic_correct: dict[str, int] = defaultdict(int)
    for row in results:
        if row["is_correct"]:
            topic_correct[row["topic"]] += 1

    for topic in sorted(topic_totals):
        topic_accuracy = (topic_correct[topic] / topic_totals[topic]) * 100
        print(
            f"- {topic}: {topic_correct[topic]}/{topic_totals[topic]} "
            f"({topic_accuracy:.2f}%)"
        )


def main() -> None:
    print("[1/4] Loading configuration...")
    load_env(ENV_PATH)

    api_key = required_env("OLLAMA_API_KEY")
    base_url = env_value("OLLAMA_CHAT_BASE_URL", DEFAULT_BASE_URL)
    chat_path = env_value("OLLAMA_CHAT_PATH", DEFAULT_CHAT_PATH)
    dataset_path = resolve_path(
        env_value("OLLAMA_EVAL_DATASET_PATH", str(DEFAULT_DATASET_PATH)),
        DEFAULT_DATASET_PATH,
    )
    results_path = resolve_path(
        env_value("OLLAMA_EVAL_RESULTS_PATH", str(DEFAULT_RESULTS_PATH)),
        DEFAULT_RESULTS_PATH,
    )
    num_predict = max(
        int_env("OLLAMA_EVAL_NUM_PREDICT", DEFAULT_NUM_PREDICT),
        MIN_NUM_PREDICT,
    )

    print(f"[2/4] Loading questions from {dataset_path}...")
    questions = load_questions(dataset_path)
    models = available_models(
        configured_models(),
        api_key,
        base_url,
        chat_path,
        num_predict,
    )
    model = select_model(models)

    print(f"[3/4] Evaluating {len(questions)} questions with {model}...")
    results: list[dict[str, Any]] = []
    total = len(questions)
    for index, question in enumerate(questions, start=1):
        expected_answer = str(question["answer"]).strip()
        try:
            model_answer, raw_response = call_ollama_mcq(
                question,
                model,
                api_key,
                base_url,
                chat_path,
                num_predict,
            )
            result = result_row(question, model, model_answer, raw_response)
        except Exception as exc:
            result = result_row(question, model, None, "", str(exc))

        results.append(result)
        status = "OK" if result["is_correct"] else "MISS"
        display_answer = result["model_answer"] or "?"
        progress = (
            f"[{index}/{total}] {question['id']} "
            f"correct={expected_answer} model={display_answer} {status}"
        )
        if result.get("error"):
            progress += f" error={result['error']}"
        print(progress)

    print(f"[4/4] Writing detailed results to {results_path}...")
    write_results(results_path, results)
    print_summary(model, results)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, KeyboardInterrupt) as exc:
        raise SystemExit(f"Error: {exc}") from exc
