# AI Application Assignments and Projects

Participant briefs for practicing embeddings, contextual chunking, Pinecone, RAG, FastAPI, browser interfaces, Docker, LangChain, LangGraph, and LLM evaluation. Each linked document defines a task and its acceptance criteria; solutions are not included.

## Suggested learning sequence

Complete assignments 01–04 to build the retrieval pipeline, 05–07 to expose and package it, 08–09 to practice graph workflows, and 10 to evaluate model behavior. Later assignments may reuse earlier deliverables. Then choose one project; completing all five projects is not required.

Estimates assume basic Python knowledge, a working development environment, and access to the required services. Model downloads and service setup can add time. Projects target one to two working days, approximately 8–16 hours.

## Assignments

| No. | Assignment | Main concepts | Difficulty | Effort |
| --- | --- | --- | --- | --- |
| 01 | [Embeddings and semantic similarity](assignments/01_embeddings_and_semantic_similarity.md) | Local embeddings, JSONL, cosine similarity | Beginner | 1–2 hours |
| 02 | [PDF to contextual chunks](assignments/02_pdf_to_contextual_chunks.md) | Docling, Markdown, heading boundaries, metadata | Beginner | 1–2 hours |
| 03 | [Pinecone upload and inspection](assignments/03_pinecone_upload_and_inspection.md) | Vector validation, upsert, namespaces, fetch | Beginner | 1–2 hours |
| 04 | [Grounded question answering](assignments/04_grounded_question_answering.md) | Retrieval, prompts, citations, insufficient evidence | Developing | 2–3 hours |
| 05 | [FastAPI RAG service](assignments/05_fastapi_rag_service.md) | File uploads, request validation, API responses | Developing | 3–4 hours |
| 06 | [Browser interface for RAG](assignments/06_browser_interface_for_rag.md) | HTML, CSS, JavaScript, fetch, dropdowns | Developing | 3–4 hours |
| 07 | [Containerize the application](assignments/07_containerize_the_application.md) | Docker, runtime configuration, networking | Developing | 2–3 hours |
| 08 | [LangChain RAG with graph nodes](assignments/08_langchain_rag_with_graph_nodes.md) | LangChain integrations, state, nodes, edges | Intermediate | 3–4 hours |
| 09 | [School tool-routing agent](assignments/09_school_tool_routing_agent.md) | Tool selection, multi-tool execution, grounded generation | Intermediate | 3–5 hours |
| 10 | [LLM evaluation harness](assignments/10_llm_evaluation_harness.md) | Exact-match grading, judge models, grouped metrics | Intermediate | 3–5 hours |

## Projects

| No. | Project | Main concepts | Difficulty | Effort |
| --- | --- | --- | --- | --- |
| 01 | [Campus handbook assistant](projects/01_campus_handbook_assistant.md) | PDF ingestion, RAG, API, cited chat UI | Intermediate | 8–12 hours |
| 02 | [School operations assistant](projects/02_school_operations_assistant.md) | LangGraph, four tools, model routing, evidence | Intermediate | 8–16 hours |
| 03 | [LLM evaluation workbench](projects/03_llm_evaluation_workbench.md) | Model selection, judge evaluation, comparison reports | Intermediate | 8–16 hours |
| 04 | [Multi-document knowledge explorer](projects/04_multi_document_knowledge_explorer.md) | Document namespaces, browsing, retrieval isolation | Intermediate | 8–16 hours |
| 05 | [Support triage assistant](projects/05_support_triage_assistant.md) | Tool-routing graph, mock services, human review | Intermediate | 8–16 hours |

## Environment and working conventions

- Use Python 3.11 and an isolated environment. Document portable commands using `python`, relative paths, and project-specific requirements.
- Keep your implementation in your own working directory or branch. Existing scripts are references; they are not guaranteed to meet every exercise requirement. Do not overwrite the supplied datasets or shared demo vectors.
- Use synthetic or public documents and fictional records. Any PDF needed for assessment must be supplied with your submission or reproducible from your included source text; local `source/` files may be absent from a fresh checkout.
- Load credentials from `.env` or runtime environment variables. Submit `.env.example` containing placeholders, never real credentials. Exclude `.env`, generated vectors, local processing files, and virtual environments from version control.
- Use local Ollama for embeddings and Ollama Cloud for generation. Make model names configurable and check which models your account can call before a full run. Cloud access may require credits.
- Match the Pinecone index dimension to the embedding model. The course's `nomic-embed-text` workflow expects 768 dimensions; validate the actual response. Use the same embedding model for stored documents and queries.
- Use a dedicated named Pinecone namespace such as `participant-01-a03`; keep every query, upload, and fetch scoped to it. Do not delete or alter other participants' records.
- Capture enough output to verify the acceptance criteria. For model responses, assess supported facts and source references rather than exact wording. Clearly label unavailable-service tests and simulated failures.

## Reference map

| Concept | Existing learning material |
| --- | --- |
| PDF conversion and chunking | [PDF conversion](../convert_pdf_to_md.py), [heading chunker](../chunk_md_to_jsonl.py) |
| Embedding and vector storage | [Ollama embeddings](../ollama_embed_texts.py), [Pinecone upload](../upload_to_pinecone.py) |
| Retrieval and grounded answers | [Query script](../query_pinecone.py), [answer script](../answer_with_context.py) |
| HTTP and browser interfaces | [API routes](../backend/app/api/routes.py), [static UI](../backend/app/static/) |
| Containers | [Dockerfile](../Dockerfile), [Docker exclusions](../.dockerignore) |
| Graph-based RAG | [LangChain RAG graph](../langchain/rag_query.py) |
| Dummy school tools and routing | [School agent](../langGraph/school_agent_graph.py), [school sample data](../langGraph/sample_school_data.py) |
| Model evaluation | [MCQ evaluator](../LLM_evaluation/evaluate_ollama_mcq.py), [constraint evaluator](../LLM_evaluation/evaluate_instruction_constraints.py) |

## Submission expectations

For each assignment, submit the requested implementation, sample inputs, sanitized evidence, and a short run guide. Every project has its own final submission checklist. Explain limitations honestly, including dummy tools, missing data, model variability, and judge uncertainty.
