# Assignment 06: Browser Interface for RAG

**Difficulty:** Developing  
**Estimated effort:** 3–4 hours

## Scenario

Nontechnical users need to upload college documents, ask questions, and inspect the evidence. Build a small browser interface served by the same FastAPI application.

## Learning objectives

- Send multipart and JSON requests with browser `fetch()`.
- Populate dependent dropdowns from live API data.
- Render answers and metadata with useful waiting and error states.

## Prerequisites

Assignment 05 or the supplied backend with ingestion, chat, and Pinecone viewer endpoints. Reference: [existing static UI](../../backend/app/static/).

## Requirements

1. Create three linked pages: PDF upload, grounded chat, and stored chunk viewer. Use plain HTML, CSS, and JavaScript without a frontend build system.
2. On every page, use index and namespace dropdowns populated from `GET /pinecone/indexes` and `GET /pinecone/namespaces?index_name=...`. Changing the index must clear the old namespace selection and load the new values. Extend the backend with read-only discovery routes if needed.
3. The upload page sends a PDF and selected destination to `/ingest/pdf`, then shows run ID, vector count, index, and namespace.
4. The chat page accepts a question and positive integer `top_k`, calls `/chat`, and displays the answer before ranked chunks with IDs, scores, and text.
5. The viewer calls `/pinecone/chunks` for the selection and displays chunk IDs, headings, source metadata, and text without vectors.
6. Disable submission while waiting or while no valid destination is available. Show empty-state, validation, server, and network messages. Render document and model text safely as text rather than executable HTML.

## Sample input and expected behavior

Select an index and a namespace containing a campus guide, then ask “When does the library close?” Expect the returned answer and source cards. Switch indexes: a namespace from the first index must not remain selected silently.

Try a `.txt` upload, an empty question, and a simulated API failure. Each must show a readable message, and controls must become usable again after a failure.

## Deliverables

Submit the static pages and any discovery-route additions, startup instructions, and screenshots or a short recording of all three workflows.

## Acceptance criteria

- All three pages load from FastAPI and link to one another.
- Dropdown contents come from API responses, with no hardcoded index or namespace options.
- Valid upload, chat, and chunk-view requests send the selected destination.
- An index with no namespaces shows an empty state and prevents invalid submission.
- Loading and failure demonstrations recover without refreshing; HTML-like text displays without executing.
