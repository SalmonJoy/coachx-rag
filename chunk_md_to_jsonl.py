import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE = ROOT / "source" / "md" / "RAG demo.md"
DEFAULT_OUTPUT = ROOT / "source" / "chunks" / "RAG demo.jsonl"
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
IMAGE_COMMENT_PATTERN = re.compile(r"<!--\s*image\s*-->", re.IGNORECASE)


def resolve_path(raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = ROOT / path
    return path


def cli_paths() -> tuple[Path, Path]:
    if len(sys.argv) > 3:
        raise RuntimeError(
            "Usage: python chunk_md_to_jsonl.py [input_md] [output_jsonl]"
        )

    source = resolve_path(sys.argv[1]) if len(sys.argv) >= 2 else DEFAULT_SOURCE
    output = resolve_path(sys.argv[2]) if len(sys.argv) >= 3 else DEFAULT_OUTPUT
    return source, output


def relative_posix_path(path: Path) -> str:
    try:
        relative = path.resolve().relative_to(ROOT.resolve())
    except ValueError:
        relative = path.resolve()

    return relative.as_posix()


def slug_from_path(path: Path) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", path.stem.lower()).strip("-")
    return slug or "chunk"


def meaningful_text(markdown: str) -> str:
    lines = []
    for line in markdown.splitlines():
        if HEADING_PATTERN.match(line):
            continue

        cleaned = IMAGE_COMMENT_PATTERN.sub("", line).strip()
        if cleaned:
            lines.append(cleaned)

    return "\n".join(lines).strip()


def finalize_chunk(
    chunk: dict[str, Any] | None,
    end_line: int,
    source_file: str,
    chunk_index: int,
    chunk_prefix: str,
) -> dict[str, Any] | None:
    if chunk is None:
        return None

    body = "\n".join(chunk.pop("_body_lines")).strip()
    text = meaningful_text(body)
    if not text:
        return None

    content = f"{chunk['_heading_line']}\n\n{body}".strip()
    return {
        "chunk_id": f"{chunk_prefix}-{chunk_index:03d}",
        "source_file": source_file,
        "heading": chunk["heading"],
        "heading_level": chunk["heading_level"],
        "content": content,
        "text": text,
        "start_line": chunk["start_line"],
        "end_line": end_line,
    }


def chunk_markdown(source: Path) -> list[dict[str, Any]]:
    if not source.exists():
        raise FileNotFoundError(f"Markdown file not found: {source}")

    source_file = relative_posix_path(source)
    chunk_prefix = slug_from_path(source)
    chunks: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    chunk_index = 1

    lines = source.read_text(encoding="utf-8").splitlines()
    for line_number, line in enumerate(lines, start=1):
        heading_match = HEADING_PATTERN.match(line)
        if heading_match:
            finalized = finalize_chunk(
                current,
                line_number - 1,
                source_file,
                chunk_index,
                chunk_prefix,
            )
            if finalized:
                chunks.append(finalized)
                chunk_index += 1

            hashes, heading = heading_match.groups()
            current = {
                "_heading_line": line,
                "_body_lines": [],
                "heading": heading.strip(),
                "heading_level": len(hashes),
                "start_line": line_number,
            }
            continue

        if current is not None:
            current["_body_lines"].append(line)

    finalized = finalize_chunk(
        current,
        len(lines),
        source_file,
        chunk_index,
        chunk_prefix,
    )
    if finalized:
        chunks.append(finalized)

    return chunks


def write_jsonl(chunks: list[dict[str, Any]], output: Path) -> None:
    if not chunks:
        raise RuntimeError("No meaningful chunks were generated")

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as file:
        for chunk in chunks:
            file.write(json.dumps(chunk, ensure_ascii=False) + "\n")


def main() -> None:
    source, output = cli_paths()

    print(f"[1/3] Reading Markdown: {source}")
    chunks = chunk_markdown(source)

    print(f"[2/3] Writing JSONL chunks: {output}")
    write_jsonl(chunks, output)

    print(f"[3/3] Done. Wrote {len(chunks)} chunks.")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, RuntimeError) as exc:
        raise SystemExit(f"Error: {exc}") from exc
