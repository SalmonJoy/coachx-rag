import os
from pathlib import Path

from google import genai
from google.genai import errors


ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"
TEXT_PATH = ROOT / "sample_embedding_text.txt"


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


def load_text_lines(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Missing text file: {path}")

    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> None:
    load_env(ENV_PATH)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY was not found in .env or environment.")

    texts = load_text_lines(TEXT_PATH)
    if not texts:
        raise RuntimeError(f"No text lines found in {TEXT_PATH}")

    client = genai.Client(api_key=api_key)
    try:
        result = client.models.embed_content(
            model="gemini-embedding-2",
            contents=texts,
        )
    except errors.APIError as exc:
        raise SystemExit(f"Gemini API error: {exc}") from exc

    print(f"Embedded {len(result.embeddings)} text lines from {TEXT_PATH.name}")

    for index, embedding in enumerate(result.embeddings, start=1):
        values = embedding.values
        preview = ", ".join(f"{value:.5f}" for value in values[:8])
        print(f"{index}. dimensions={len(values)} preview=[{preview}, ...]")


if __name__ == "__main__":
    main()
