# Project 01: Campus Handbook Assistant

**Difficulty:** Intermediate  
**Estimated effort:** 8–12 hours

## Scenario

Northbridge College, a fictional institution, wants students to ask questions about its handbook. Build an application that ingests a handbook PDF and answers from its actual contents, with evidence that a student can inspect.

## Learning objectives

- Integrate PDF conversion, contextual chunking, embeddings, and Pinecone.
- Expose ingestion and grounded chat through FastAPI and a browser interface.
- Demonstrate traceable answers and honest handling of missing information.

## Prerequisites

Assignments 02–06 or equivalent knowledge. Use local Ollama embeddings, an accessible Ollama Cloud chat model, Pinecone, and FastAPI. The [existing backend](../../backend/app/) is reference material. Follow the [shared working conventions](../README.md#environment-and-working-conventions).

## Minimum implementation requirements

1. Supply a synthetic handbook PDF with at least six meaningful sections covering library hours, transport, enrollment, facilities, student clubs, and support contacts. Include at least one nested heading and retain an editable source version.
2. Convert it with Docling, chunk by headings, embed meaningful sections, and upload to a dedicated named namespace. Preserve stable source IDs, headings, document identity, and Markdown line ranges.
3. Expose PDF ingestion and chat APIs. Isolate processing artifacts per run and report the actual destination and confirmed upload count.
4. Provide linked upload and chat pages, with API-populated index/namespace dropdowns, waiting states, and readable errors.
5. Answer using only retrieved text, cite chunk IDs, and display source chunks. Return an insufficient-information response when the handbook does not support an answer.
6. Document a reproducible local startup, configurable model names, and a sanitized environment template. Keep credentials on the server.

## Sample inputs and demonstration scenarios

Include these facts in your fictional handbook: the library closes at 8 PM on weekdays, the shuttle stops at the north gate, and the robotics club meets on Wednesdays.

| Scenario | Input or action | Observable expected behavior |
| --- | --- | --- |
| Successful ingestion | Upload the handbook to your project namespace | A unique run ID, saved artifacts, and confirmed vector count are returned. |
| Supported answer | “Where should I wait for the campus shuttle?” | Answer identifies the north gate and cites a retrieved handbook chunk. |
| Another supported answer | “When does the robotics club meet?” | Answer uses the Wednesday fact and shows its source. |
| Missing information | “What is the dean's private mobile number?” | Answer explains that this information is not in the handbook. |
| Validation failure | Upload a `.txt` file through the PDF form | A readable client error appears; submission controls recover. |
| Service failure | Simulate an unavailable embedding server | The request fails clearly and does not claim successful ingestion. |

Also prepare a ten-question review set containing six supported and four unsupported questions. Record retrieved IDs and manually check whether each answer is supported; exact wording is not graded.

## Deliverables

Submit the application, sample PDF and editable source, dependencies, configuration template, local run guide, ten-question review results, and a short demonstration recording or equivalent screenshots/transcripts. Package generated ingestion artifacts separately from version-controlled source.

## Acceptance criteria

- A fresh setup can ingest the included PDF and answer the review questions without relying on an existing shared namespace.
- Every displayed citation resolves to a retrieved chunk with matching handbook text.
- Unsupported questions do not invent contacts, policies, or schedules.
- Ingestion records and chat responses agree on index and namespace.
- Both validation and service-failure demonstrations produce readable feedback without leaking credentials.

## Submission checklist

- [ ] Source, dependencies, and a placeholder-only `.env.example` are included.
- [ ] Synthetic PDF, editable source, and setup commands are reproducible.
- [ ] Upload and chat workflows are demonstrated.
- [ ] Review set includes supported and unsupported questions with evidence.
- [ ] Failure demonstrations and known limitations are documented.
- [ ] No secrets, real student records, or generated vectors are committed.
