# Project 04: Multi-Document Knowledge Explorer

**Difficulty:** Intermediate  
**Estimated effort:** 8–16 hours

## Scenario

An organization maintains several guides with similar vocabulary but different rules. Build a browser application that lets users select a document collection, inspect its chunks, and ask questions without mixing evidence from another collection.

## Learning objectives

- Organize vector data into distinct document namespaces.
- Preserve document identity through ingestion and retrieval.
- Demonstrate collection isolation when documents contain conflicting facts.

## Prerequisites

Assignments 02–06 or equivalent ingestion, Pinecone, API, and browser experience. Reference: [Pinecone viewer service](../../backend/app/services/pinecone_viewer.py) and [static pages](../../backend/app/static/). Use the same compatible embedding model across the chosen index.

## Minimum implementation requirements

1. Supply three synthetic PDFs with at least four meaningful sections each: a North Campus Guide, a South Campus Guide, and a Workshop Guide. Keep editable source versions.
2. Ingest each PDF into its own dedicated named namespace in one existing index. For this project, one document is one collection; do not require cross-collection search or merged answers.
3. Retain document identity, heading, source location, text, embedding model, and stable chunk IDs. Re-uploading an unchanged document to its namespace must reuse IDs; it must not modify another namespace.
4. Provide upload, browse, and chat pages. Always load available index and namespace choices from read-only discovery APIs; clear dependent selections when the index changes. Do not offer editing or deletion of vectors.
5. Show chunk ID, heading, source file/line range, model, and text. Load up to 100 chunks per request, label that limit, and distinguish an empty collection from a failed request. Never return vector values from the viewer API.
6. Scope every list, fetch, and query to the selected namespace. Display the selected destination alongside answers and source cards; prevent stale answers from being presented as belonging to a newly selected collection.
7. Generate answers only from the selected collection and explicitly acknowledge missing information.

## Sample inputs and demonstration scenarios

Set the North Campus library closing time to 8 PM and the South Campus time to 6 PM. The Workshop Guide should describe workshop registration and contain no library-hours policy.

| Scenario | Input or action | Observable expected behavior |
| --- | --- | --- |
| First collection | Select North Campus; ask “When does the library close?” | Answer says 8 PM and cites North Campus evidence. |
| Conflicting collection | Select South Campus; ask the same question | Answer says 6 PM and cites South Campus evidence only. |
| Missing information | Select Workshop Guide; ask the same question | Answer states that library hours are not provided. |
| Browse and verify | Load chunks in each collection | Headings and source labels match only the selected PDF. |
| Repeat upload | Re-upload the unchanged North Campus PDF | Known IDs remain stable; South Campus records remain unchanged. |
| Empty selection | Select an index with no available namespaces, using a controlled API response if necessary | Empty-state feedback appears and invalid submission is prevented. |
| Service failure | Simulate a namespace-discovery or fetch failure | A readable error appears, with no stale data presented as current. |

## Deliverables

Submit the application, three PDFs and editable sources, configuration/dependencies, startup guide, a namespace/document mapping, and evidence from all isolation scenarios. Include a small verification report comparing returned source IDs with the selected collection.

## Acceptance criteria

- All three documents can be ingested, browsed, and queried independently.
- The two conflicting-fact questions return the selected document's fact with valid sources.
- Missing-information answers do not borrow facts from other namespaces.
- Re-upload evidence demonstrates stable IDs without cross-namespace changes.
- Empty/error states are distinct, browser selections are consistent, and viewer responses omit vectors.

## Submission checklist

- [ ] Three reproducible synthetic documents and dedicated namespace names are listed.
- [ ] Ingestion, browsing, and chat are available through the UI.
- [ ] Dropdown values are loaded dynamically from the backend.
- [ ] Conflicting-fact, unsupported-query, and repeat-upload evidence is provided.
- [ ] Empty-state and service-failure demonstrations are included.
- [ ] Credentials and generated processing/vector artifacts are excluded from source control.
