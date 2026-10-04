import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"

DEFAULT_DATASET_PATH = ROOT / "LLM_evaluation" / "instruction_constraints_eval.jsonl"
DEFAULT_RESULTS_PATH = ROOT / "LLM_evaluation" / "instruction_constraint_eval_results.jsonl"
DEFAULT_BASE_URL = "https://ollama.com"
DEFAULT_CHAT_PATH = "/api/chat"
DEFAULT_GENERATE_NUM_PREDICT = 300
DEFAULT_JUDGE_NUM_PREDICT = 300
DEFAULT_TEMPERATURE = 0
MIN_NUM_PREDICT = 64

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


def load_tasks(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise RuntimeError(f"Dataset file does not exist: {path}")

    tasks: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Invalid JSON on line {line_number}: {exc}") from exc

            validate_task(row, line_number)
            tasks.append(row)

    if not tasks:
        raise RuntimeError(f"No tasks found in dataset: {path}")

    return tasks


def validate_task(row: dict[str, Any], line_number: int) -> None:
    required_fields = ["id", "category", "instruction", "constraints", "judge_checks"]
    missing = [field for field in required_fields if field not in row]
    if missing:
        raise RuntimeError(f"Line {line_number} is missing fields: {', '.join(missing)}")

    if not isinstance(row["constraints"], list) or not row["constraints"]:
        raise RuntimeError(f"Line {line_number} constraints must be a non-empty list")

    if not isinstance(row["judge_checks"], list) or not row["judge_checks"]:
        raise RuntimeError(f"Line {line_number} judge_checks must be a non-empty list")


def chat_response_content(payload: dict[str, Any]) -> str:
    if isinstance(payload.get("message"), dict):
        return str(payload["message"].get("content", "")).strip()

    if isinstance(payload.get("choices"), list) and payload["choices"]:
        message = payload["choices"][0].get("message", {})
        return str(message.get("content", "")).strip()

    return ""


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


def post_chat(
    model: str,
    messages: list[dict[str, str]],
    api_key: str,
    base_url: str,
    chat_path: str,
    num_predict: int,
    timeout: int = 120,
) -> str:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearer_token(api_key)}",
    }
    url = f"{base_url.rstrip('/')}/{chat_path.lstrip('/')}"
    body = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": DEFAULT_TEMPERATURE,
            "num_predict": num_predict,
        },
    }

    try:
        response = requests.post(url, json=body, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        raise RuntimeError(f"Request failed: {exc}") from exc

    if response.status_code != 200:
        raise RuntimeError(
            f"Ollama returned HTTP {response.status_code}: {short_error(response)}"
        )

    content = chat_response_content(response.json())
    if not content:
        raise RuntimeError("Ollama returned an empty chat response")

    return content


def check_model_available(
    model: str,
    api_key: str,
    base_url: str,
    chat_path: str,
    num_predict: int,
) -> tuple[bool, str]:
    try:
        post_chat(
            model,
            [{"role": "user", "content": "Reply with exactly: OK"}],
            api_key,
            base_url,
            chat_path,
            num_predict,
            timeout=45,
        )
    except RuntimeError as exc:
        return False, str(exc)

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


def select_model(models: list[str], prompt: str) -> str:
    print("Available Ollama Cloud models:")
    for index, model in enumerate(models, start=1):
        print(f"{index}. {model}")

    while True:
        selected = input(prompt).strip()
        try:
            selected_index = int(selected)
        except ValueError:
            print("Please enter a valid number.")
            continue

        if 1 <= selected_index <= len(models):
            return models[selected_index - 1]

        print(f"Please choose a number from 1 to {len(models)}.")


def bullet_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def generate_response(
    task: dict[str, Any],
    model: str,
    api_key: str,
    base_url: str,
    chat_path: str,
    num_predict: int,
) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are completing an instruction-following evaluation task. "
                "Follow every constraint exactly. Return only the requested response."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Instruction:\n{task['instruction']}\n\n"
                f"Constraints:\n{bullet_list(task['constraints'])}\n\n"
                "Write the response now."
            ),
        },
    ]
    return post_chat(model, messages, api_key, base_url, chat_path, num_predict)


def extract_json_payload(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    try:
        payload = json.loads(cleaned)
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        pass

    object_start = cleaned.find("{")
    object_end = cleaned.rfind("}")
    if object_start != -1 and object_end != -1 and object_end > object_start:
        payload = json.loads(cleaned[object_start : object_end + 1])
        if isinstance(payload, dict):
            return payload

    raise RuntimeError("Judge response did not contain a JSON object")


def normalize_judge_result(payload: dict[str, Any]) -> dict[str, Any]:
    passed = bool(payload.get("passed", False))

    try:
        score = float(payload.get("score", 1.0 if passed else 0.0))
    except (TypeError, ValueError):
        score = 1.0 if passed else 0.0
    score = max(0.0, min(score, 1.0))

    failed_checks = payload.get("failed_checks", [])
    if not isinstance(failed_checks, list):
        failed_checks = [str(failed_checks)]

    reason = str(payload.get("reason", "")).strip()
    if not reason:
        reason = "No reason provided by judge."

    return {
        "passed": passed,
        "score": score,
        "failed_checks": [str(item) for item in failed_checks],
        "reason": reason,
    }


def judge_response(
    task: dict[str, Any],
    model_response: str,
    judge_model: str,
    api_key: str,
    base_url: str,
    chat_path: str,
    num_predict: int,
) -> tuple[dict[str, Any], str]:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a strict judge for instruction-following evaluations. "
                "Evaluate only whether the model response satisfies the listed "
                "constraints and judge checks. Return valid JSON only."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Instruction:\n{task['instruction']}\n\n"
                f"Constraints:\n{json.dumps(task['constraints'], ensure_ascii=False)}\n\n"
                f"Judge checks:\n{json.dumps(task['judge_checks'], ensure_ascii=False)}\n\n"
                f"Model response:\n{model_response}\n\n"
                "Return only this JSON shape:\n"
                "{\n"
                '  "passed": true,\n'
                '  "score": 1.0,\n'
                '  "failed_checks": [],\n'
                '  "reason": "All constraints were followed."\n'
                "}\n"
                "Use score from 0.0 to 1.0."
            ),
        },
    ]
    raw_response = post_chat(
        judge_model,
        messages,
        api_key,
        base_url,
        chat_path,
        num_predict,
    )
    return normalize_judge_result(extract_json_payload(raw_response)), raw_response


def failed_judge_result(reason: str) -> dict[str, Any]:
    return {
        "passed": False,
        "score": 0.0,
        "failed_checks": ["evaluation_error"],
        "reason": reason,
    }


def result_row(
    task: dict[str, Any],
    evaluated_model: str,
    judge_model: str,
    model_response: str,
    judge_result: dict[str, Any],
    raw_judge_response: str,
    error: str | None = None,
) -> dict[str, Any]:
    row = {
        "id": task["id"],
        "category": task["category"],
        "evaluated_model": evaluated_model,
        "judge_model": judge_model,
        "instruction": task["instruction"],
        "constraints": task["constraints"],
        "judge_checks": task["judge_checks"],
        "model_response": model_response,
        "judge_result": judge_result,
        "raw_judge_response": raw_judge_response,
        "is_passed": bool(judge_result.get("passed", False)),
    }
    if error:
        row["error"] = error

    return row


def write_results(path: Path, results: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        for row in results:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def print_summary(
    evaluated_model: str,
    judge_model: str,
    results: list[dict[str, Any]],
) -> None:
    total = len(results)
    passed = sum(1 for row in results if row["is_passed"])
    pass_rate = (passed / total) * 100 if total else 0
    average_score = (
        sum(float(row["judge_result"].get("score", 0.0)) for row in results) / total
        if total
        else 0.0
    )

    print()
    print("Constraint evaluation summary")
    print(f"Evaluated model: {evaluated_model}")
    print(f"Judge model: {judge_model}")
    print(f"Total tasks: {total}")
    print(f"Passed: {passed}")
    print(f"Pass rate: {pass_rate:.2f}%")
    print(f"Average judge score: {average_score:.2f}")
    print()
    print("Per-category pass rate:")

    category_totals = Counter(row["category"] for row in results)
    category_passed: dict[str, int] = defaultdict(int)
    for row in results:
        if row["is_passed"]:
            category_passed[row["category"]] += 1

    for category in sorted(category_totals):
        category_rate = (category_passed[category] / category_totals[category]) * 100
        print(
            f"- {category}: {category_passed[category]}/{category_totals[category]} "
            f"({category_rate:.2f}%)"
        )


def main() -> None:
    print("[1/5] Loading configuration...")
    load_env(ENV_PATH)

    api_key = required_env("OLLAMA_API_KEY")
    base_url = env_value("OLLAMA_CHAT_BASE_URL", DEFAULT_BASE_URL)
    chat_path = env_value("OLLAMA_CHAT_PATH", DEFAULT_CHAT_PATH)
    dataset_path = resolve_path(
        env_value("OLLAMA_CONSTRAINT_DATASET_PATH", str(DEFAULT_DATASET_PATH)),
        DEFAULT_DATASET_PATH,
    )
    results_path = resolve_path(
        env_value("OLLAMA_CONSTRAINT_RESULTS_PATH", str(DEFAULT_RESULTS_PATH)),
        DEFAULT_RESULTS_PATH,
    )
    generate_num_predict = max(
        int_env(
            "OLLAMA_CONSTRAINT_GENERATE_NUM_PREDICT",
            DEFAULT_GENERATE_NUM_PREDICT,
        ),
        MIN_NUM_PREDICT,
    )
    judge_num_predict = max(
        int_env("OLLAMA_CONSTRAINT_JUDGE_NUM_PREDICT", DEFAULT_JUDGE_NUM_PREDICT),
        MIN_NUM_PREDICT,
    )

    print(f"[2/5] Loading tasks from {dataset_path}...")
    tasks = load_tasks(dataset_path)

    models = available_models(
        configured_models(),
        api_key,
        base_url,
        chat_path,
        max(generate_num_predict, judge_num_predict),
    )
    evaluated_model = select_model(models, "Select evaluated model by number: ")
    judge_model = select_model(models, "Select judge model by number: ")

    print(f"[3/5] Generating and judging {len(tasks)} constrained responses...")
    results: list[dict[str, Any]] = []
    total = len(tasks)
    for index, task in enumerate(tasks, start=1):
        model_response = ""
        raw_judge_response = ""
        error = None

        try:
            model_response = generate_response(
                task,
                evaluated_model,
                api_key,
                base_url,
                chat_path,
                generate_num_predict,
            )
            judge_result, raw_judge_response = judge_response(
                task,
                model_response,
                judge_model,
                api_key,
                base_url,
                chat_path,
                judge_num_predict,
            )
        except Exception as exc:
            error = str(exc)
            judge_result = failed_judge_result(error)

        result = result_row(
            task,
            evaluated_model,
            judge_model,
            model_response,
            judge_result,
            raw_judge_response,
            error,
        )
        results.append(result)

        status = "PASS" if result["is_passed"] else "FAIL"
        score = float(result["judge_result"].get("score", 0.0))
        progress = f"[{index}/{total}] {task['id']} {status} score={score:.2f}"
        if error:
            progress += f" error={error}"
        print(progress)

    print(f"[4/5] Writing detailed results to {results_path}...")
    write_results(results_path, results)

    print("[5/5] Summary:")
    print_summary(evaluated_model, judge_model, results)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, KeyboardInterrupt) as exc:
        raise SystemExit(f"Error: {exc}") from exc
