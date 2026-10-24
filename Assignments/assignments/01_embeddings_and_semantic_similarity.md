# Assignment 01: Embeddings and Semantic Similarity

**Difficulty:** Beginner  
**Estimated effort:** 1–2 hours

## Scenario

A college wants to find relevant help articles even when students use different words from the articles. Build a small semantic-search experiment before introducing a vector database.

## Learning objectives

- Generate local Ollama embeddings and understand vector dimensions.
- Store text and vectors together in JSONL.
- Rank text using cosine similarity and explain the results.

## Prerequisites

Basic Python, JSON, HTTP requests, and local Ollama with an embedding model. Reference: [embedding script](../../ollama_embed_texts.py). Follow the [shared working conventions](../README.md#environment-and-working-conventions).

## Requirements

1. Prepare at least 10 short articles spanning at least three topics, such as library access, transport, and enrollment. Give every article a unique ID.
2. Embed each article with a configurable local model, defaulting to `nomic-embed-text`.
3. Write UTF-8 JSONL records containing `chunk_id`, `text`, `embedding_model`, and `values`. Validate the response count, numeric values, and consistent dimensions.
4. Accept a user query, embed it with the same model, and print the three highest cosine similarities with IDs and article text. Implement the comparison locally without Pinecone.
5. Reject empty queries and handle an unavailable Ollama server with a readable message.

## Sample input and expected behavior

Include articles such as “The library stays open until 8 PM on weekdays” and “The campus shuttle stops at the north gate.” Try:

- “Where can I study in the evening?”
- “How do I travel to the north gate?”
- “How do I enroll in a course?”

Include an enrollment article for the third query. Expect three ranked results per query; discuss whether the relevant article ranks highly. Similarity alone does not establish that an answer is supported.

## Deliverables

Submit the input texts, embedding/search implementation, dependency list, run instructions, and a short report containing the three searches. Provide generated vectors as a separate local artifact, excluded from Git.

## Acceptance criteria

- At least 10 records load successfully and have unique IDs and equal nonzero vector lengths.
- Search prints exactly three distinct IDs in descending similarity order.
- Query and article embeddings use the same model; dimension mismatches are rejected.
- The report identifies at least one useful match and one limitation of semantic similarity.
- Empty-query and unavailable-server demonstrations produce readable failures without exposing credentials.
