# Assignment 03: Pinecone Upload and Inspection

**Difficulty:** Beginner  
**Estimated effort:** 1–2 hours

## Scenario

Your college help articles have embeddings. Store them in a searchable vector database and demonstrate that their text and source metadata can be recovered intact.

## Learning objectives

- Map embedding records to Pinecone vectors.
- Validate a complete input before making writes.
- Use namespaces, stable IDs, upsert, and fetch.

## Prerequisites

Assignment 01, or at least 10 equivalent JSONL embedding records; a Pinecone API key and an existing index matching the embedding dimension. Reference: [upload script](../../upload_to_pinecone.py).

## Requirements

1. Load API credentials, index name, namespace, expected dimension, and batch size from configuration. Use a dedicated named participant namespace.
2. Read JSONL and validate every record before uploading: unique nonempty `chunk_id`, nonempty `text`, and a finite numeric `values` list of the expected dimension.
3. Upsert stable vector IDs, retaining text, source file, heading when available, and embedding model in metadata. Provide sensible source/heading metadata if using Assignment 01 articles.
4. Upload in batches and report confirmed upsert counts. Fetch at least two known IDs and display their metadata and vector lengths, without dumping whole vectors.
5. Re-run the same upload and verify that the known IDs remain stable rather than generating duplicate records.

## Sample input and expected behavior

Use a record with ID `library-001`, text “The library stays open until 8 PM on weekdays,” and its actual embedding. Target a namespace such as `participant-01-a03`.

Fetching `library-001` must return the same text and model metadata. In a copy of the input, shorten one vector by one value: the upload must reject that file before making any upsert calls. Repeat with a duplicate ID.

## Deliverables

Submit the uploader/inspection implementation, sanitized configuration template, run guide, and evidence of a first upload, repeat upload, fetched metadata, and rejected input.

## Acceptance criteria

- All valid input records receive confirmed upserts in the intended index and namespace.
- Two fetched IDs match their input text and vector dimension.
- Re-running preserves the IDs and contents; demonstrate using fetch or the scoped ID list, allowing for database visibility delays.
- Bad dimensions and duplicate IDs fail before any upload.
- Authentication/index errors are readable and do not print keys.
