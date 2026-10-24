# Assignment 07: Containerize the Application

**Difficulty:** Developing  
**Estimated effort:** 2–3 hours

## Scenario

A teammate should be able to run your RAG API without installing its Python dependencies directly on their machine. Package the application while keeping Ollama and Pinecone external.

## Learning objectives

- Build an image with reproducible application dependencies.
- Supply secrets at runtime and control the build context.
- Connect a containerized API to external services and persist upload artifacts.

## Prerequisites

Assignment 05, optionally Assignment 06, Docker, and access to external Ollama/Pinecone services. Reference: [project Dockerfile](../../Dockerfile).

## Requirements

1. Create a Dockerfile using Python 3.11 slim, install application dependencies, and include every module imported by the backend. Include required system libraries for PDF conversion.
2. Start Uvicorn on `0.0.0.0:8000`. Add `.dockerignore` entries for `.env`, Git metadata, caches, virtual environments, generated vectors, uploaded documents, and processing runs.
3. Supply credentials and model settings at runtime with `--env-file`. Document how `OLLAMA_HOST` reaches the host on Docker Desktop and how users on other Docker hosts provide a reachable address.
4. Mount a volume for generated run files and demonstrate that a known artifact survives container recreation.
5. Document build, run, health-check, and stop commands. Do not include an Ollama server in this image.

## Sample input and expected behavior

Document commands equivalent to `docker build -t participant-rag .` and running it with host port 8000, a runtime environment file, and a run-data volume. On Docker Desktop, an embedding URL may be `http://host.docker.internal:11434`.

Expect `http://127.0.0.1:8000/health` to report `ok`. A healthy API alone does not prove downstream connectivity: also demonstrate a document-backed chat request with reachable Ollama and Pinecone.

## Deliverables

Submit Docker configuration, a sanitized environment template, a run guide, and evidence for health, downstream access, excluded secrets, and volume persistence.

## Acceptance criteria

- A fresh build succeeds and starts without development reload mode.
- The API is reachable on the published host port; UI pages load if included.
- `.env` is excluded from the image, and required secrets arrive only at runtime.
- Grounded chat reaches the configured external services.
- Generated data survives recreation with the same volume.
- An invalid Ollama address produces a readable application error while health remains responsive.
