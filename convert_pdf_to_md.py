import sys
from pathlib import Path

from docling.document_converter import DocumentConverter


ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE = ROOT / "source" / "pdf" / "RAG demo.pdf"
DEFAULT_OUTPUT = ROOT / "source" / "md" / "RAG demo.md"


def resolve_path(raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = ROOT / path
    return path


def cli_paths() -> tuple[Path, Path]:
    if len(sys.argv) > 3:
        raise RuntimeError(
            "Usage: python convert_pdf_to_md.py [input_pdf] [output_md]"
        )

    source = resolve_path(sys.argv[1]) if len(sys.argv) >= 2 else DEFAULT_SOURCE
    output = resolve_path(sys.argv[2]) if len(sys.argv) >= 3 else DEFAULT_OUTPUT
    return source, output


def convert_pdf_to_markdown(source: Path, output: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Input PDF not found: {source}")

    output.parent.mkdir(parents=True, exist_ok=True)

    print(f"[1/3] Loading PDF: {source}")
    print("[2/3] Converting PDF to Markdown with Docling...")

    converter = DocumentConverter()
    result = converter.convert(source)
    markdown = result.document.export_to_markdown()

    if not markdown.strip():
        raise RuntimeError("Docling produced empty Markdown output")

    output.write_text(markdown, encoding="utf-8")

    print(f"[3/3] Markdown saved: {output}")
    print(f"      Characters written: {len(markdown)}")


def main() -> None:
    source, output = cli_paths()
    convert_pdf_to_markdown(source, output)


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, RuntimeError) as exc:
        raise SystemExit(f"Error: {exc}") from exc
