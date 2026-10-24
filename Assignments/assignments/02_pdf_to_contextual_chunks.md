# Assignment 02: PDF to Contextual Chunks

**Difficulty:** Beginner  
**Estimated effort:** 1–2 hours

## Scenario

A campus guide is available only as a PDF. Prepare meaningful sections for retrieval while retaining enough information to trace each chunk to its source.

## Learning objectives

- Convert PDFs to Markdown with Docling.
- Split content at heading boundaries rather than fixed character counts.
- Preserve source metadata and identify empty sections.

## Prerequisites

Python file handling and JSONL. Install Docling and allow for initial model downloads. References: [converter](../../convert_pdf_to_md.py) and [chunker](../../chunk_md_to_jsonl.py). Use a public or synthetic PDF that you include with the submission.

## Requirements

1. Accept input PDF and output directory paths; create missing output directories.
2. Convert the PDF to UTF-8 Markdown and save it for inspection.
3. Start a new chunk at each Markdown heading of levels 1–6. A section ends immediately before the next heading of any level; do not duplicate child sections into parent chunks.
4. Keep meaningful text before the first heading as an `Introduction` chunk. Drop sections containing only whitespace or image placeholders.
5. Write one JSONL record per retained section with `chunk_id`, `source_file`, `heading`, `heading_level`, `content`, `text`, `start_line`, and `end_line`. Use one-based inclusive Markdown line numbers; use heading level 0 for an introduction.
6. Include the heading in `content` and body-only material in `text`. Print input/output paths and retained chunk count.

## Sample input and expected behavior

Use this separate Markdown fixture to check chunk boundaries independently of PDF conversion:

```markdown
# Campus Guide
## Library
Open until 8 PM on weekdays.
## Transport
The shuttle stops at the north gate.
## Gallery
<!-- image -->
```

Expect two retained chunks: Library at lines 2–3 and Transport at lines 4–5. The empty title and image-only Gallery sections do not become chunks. Also test a fixture with a meaningful introductory paragraph before the first heading.

## Deliverables

Submit the conversion/chunking implementation, sample PDF, Markdown fixture, run guide, and a brief explanation of boundary rules. Supply generated Markdown and JSONL separately from source control.

## Acceptance criteria

- A supplied PDF produces readable, nonempty Markdown and valid JSONL.
- Fixture output has exactly the two expected meaningful sections with correct line ranges.
- IDs are unique; headings and body formatting are preserved.
- Introductory text is retained, while empty sections are omitted.
- Missing files and conversion failures produce clear messages.
