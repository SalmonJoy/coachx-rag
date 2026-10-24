# Assignment 08: LangChain RAG With Graph Nodes

**Difficulty:** Intermediate  
**Estimated effort:** 3–4 hours

## Scenario

Your linear retrieval script is becoming difficult to inspect. Express the workflow as a graph with explicit state updates and an observable execution sequence.

## Learning objectives

- Use LangChain integrations for Ollama and Pinecone.
- Define typed graph state and clear node responsibilities.
- Connect nodes with edges and handle a no-evidence path.

## Prerequisites

Assignment 04, LangChain integration packages, and LangGraph. Reference: [existing RAG graph](../../langchain/rag_query.py). Use a working directory that does not shadow installed package names.

## Requirements

1. Build a LangGraph `StateGraph` with `load_config`, `retrieve_chunks`, and `generate_answer` nodes, connected from `START` to `END`.
2. Keep query, destination, retrieval settings, retrieved documents/scores, and final answer in typed state. Keep credentials in configuration/model clients rather than printed state.
3. Use `OllamaEmbeddings`, `PineconeVectorStore`, and `ChatOllama`; set the Pinecone text metadata key to `text`.
4. Default retrieval to three chunks and include stable IDs in the generation context and printed sources.
5. Add a conditional edge so retrieval with no usable text skips model generation and returns an insufficient-evidence answer. Invalid configuration must stop before external calls.
6. Print node execution progress and include a simple graph diagram in the run guide.

## Sample input and expected behavior

Ask “Which gate does the campus shuttle use?” against a namespace whose guide says “The shuttle stops at the north gate.” Expect a supported answer with the retrieved ID and a trace showing configuration, retrieval, and generation.

Repeat against an empty namespace. Expect a completed insufficient-evidence result and evidence that the generation node was not called. No empty namespace needs to be created destructively; an unused participant-scoped name is sufficient.

## Deliverables

Submit the graph script, dependencies, configuration template, state/node diagram, and transcripts for supported, unsupported, and no-match queries.

## Acceptance criteria

- The implementation uses an actual compiled `StateGraph` with named nodes and edges.
- Trace output demonstrates state flowing through the expected nodes.
- Retrieved text and IDs reach the generation prompt, and answer references resolve to those IDs.
- The no-match branch completes without a chat-model call.
- Missing credentials and retrieval failures produce readable errors rather than a fabricated answer.
