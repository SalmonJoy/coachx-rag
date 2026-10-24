# Assignment 05: FastAPI RAG Service

**Difficulty:** Developing  
**Estimated effort:** 3–4 hours

## Scenario

Your retrieval scripts work locally. Expose them as an API so a browser or another application can upload documents and ask grounded questions.

## Learning objectives

- Separate HTTP routes from ingestion and retrieval logic.
- Accept multipart PDF uploads and validated JSON requests.
- Return useful results and readable failure responses.

## Prerequisites

Assignments 02–04 or equivalent services; FastAPI and upload dependencies. Reference: [existing routes](../../backend/app/api/routes.py).

## Requirements

1. Provide `GET /health` returning an `ok` status.
2. Provide `POST /ingest/pdf` accepting multipart `file`, required `index_name`, and optional `namespace`. A blank namespace uses the configured default. Convert, chunk, embed, and upsert synchronously.
3. Isolate generated files per upload using a unique run ID. Include that ID, uploaded count, actual index, and actual namespace in the success response.
4. Provide `POST /chat` accepting `query`, `index_name`, optional `namespace`, and positive integer `top_k` defaulting to 3. Return the answer and retrieved chunks with IDs, scores, and text.
5. Keep configuration and credentials server-side. Validate empty input, invalid file extensions, and invalid `top_k`. Distinguish client errors from downstream service failures with readable HTTP errors; FastAPI's standard validation responses are acceptable.

## Sample input and expected behavior

Upload a synthetic campus PDF into `participant-01-a05`. Then submit:

```json
{"query":"When does the library close?","index_name":"<your-index>","namespace":"participant-01-a05","top_k":3}
```

Expect a grounded answer and up to three source chunks from that namespace. Uploading a `.txt` file or submitting `top_k: 0` must fail as a client error.

## Deliverables

Submit the API implementation, dependency/configuration files, portable startup instructions, sample requests, and sanitized response evidence. Document synchronous processing time.

## Acceptance criteria

- Health and interactive API documentation load locally.
- One valid PDF completes every ingestion stage; querying its namespace returns supported information.
- Two uploads have distinct run directories.
- Invalid inputs produce 4xx responses; a simulated or actual downstream outage produces a readable 5xx response.
- Neither success nor error responses expose credentials.
