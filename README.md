# Contextual Vector RAG Demo

This project is a small retrieval-augmented generation demo. It embeds a few sample CoachX text chunks with local Ollama, stores the vectors in Pinecone, retrieves the most relevant chunks for a user question, and sends those chunks to Ollama GPT-OSS to produce a grounded answer.

## What Is Included

- `sample_embedding_text.txt` - five sample text chunks.
- `ollama_embed_texts.py` - checks Ollama embedding models.
- `nomic_embeddings.csv` - generated vector CSV, ignored by Git.
- `upload_to_pinecone.py` - uploads vectors from CSV into Pinecone.
- `query_pinecone.py` - embeds a question and retrieves the top 3 Pinecone chunks.
- `answer_with_context.py` - retrieves chunks and asks GPT-OSS for a grounded answer.
- `.env.example` - environment variable template.

## Requirements

- Python 3.11
- Ollama installed and running locally
- Local Ollama embedding model:
  ```powershell
  ollama pull nomic-embed-text
  ```
- A Pinecone index with dimension `768`
- An Ollama cloud API key for GPT-OSS chat

The scripts in this workspace use this Python executable:

```powershell
C:\Users\salmo\AppData\Local\Programs\Python\Python311\python.exe
```

## Setup

Install the Python dependencies:

```powershell
C:\Users\salmo\AppData\Local\Programs\Python\Python311\python.exe -m pip install requests pinecone google-genai
```

Create `.env` from `.env.example` and fill in the real values:

```env
GEMINI_API_KEY=<Add-gemini-api-key>
OLLAMA_API_KEY=<Add-ollama-api-key>
PINECONE_API_KEY=<Add-pinecone-api-key>
PINECONE_INDEX_NAME=<Add-pinecone-index-name>
PINECONE_NAMESPACE=coachx-sample
PINECONE_CSV_PATH=nomic_embeddings.csv
PINECONE_BATCH_SIZE=100
PINECONE_EXPECTED_DIMENSION=768
OLLAMA_HOST=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text
PINECONE_TOP_K=3
OLLAMA_CHAT_BASE_URL=https://ollama.com
OLLAMA_CHAT_MODEL=gpt-oss:20b-cloud
OLLAMA_CHAT_PATH=/api/chat
OLLAMA_ANSWER_TEMPERATURE=0
OLLAMA_ANSWER_NUM_PREDICT=300
```

Do not commit `.env`; it contains API keys and is ignored by `.gitignore`.

## Run The Workflow

Start or verify Ollama:

```powershell
ollama list
```

Generate local embeddings and store them in `nomic_embeddings.csv`:

```powershell
C:\Users\salmo\AppData\Local\Programs\Python\Python311\python.exe -c "from pathlib import Path; import csv, requests; texts=[l.strip() for l in Path('sample_embedding_text.txt').read_text(encoding='utf-8').splitlines() if l.strip()]; r=requests.post('http://localhost:11434/api/embed', json={'model':'nomic-embed-text','input':texts,'truncate':True}, timeout=60); r.raise_for_status(); embeddings=r.json().get('embeddings', []); dims=len(embeddings[0]) if embeddings else 0; out=Path('nomic_embeddings.csv'); f=out.open('w', newline='', encoding='utf-8'); writer=csv.writer(f); writer.writerow(['id','text'] + [f'dim_{i}' for i in range(dims)]); [writer.writerow([i,text] + vec) for i,(text,vec) in enumerate(zip(texts, embeddings), start=1)]; f.close(); print(f'wrote {len(embeddings)} embeddings with {dims} dimensions to {out}')"
```

Upload vectors to Pinecone:

```powershell
C:\Users\salmo\AppData\Local\Programs\Python\Python311\python.exe upload_to_pinecone.py
```

Search Pinecone for top 3 chunks:

```powershell
C:\Users\salmo\AppData\Local\Programs\Python\Python311\python.exe query_pinecone.py "How does CoachX help with workout planning?"
```

Generate a grounded GPT-OSS answer from the retrieved chunks:

```powershell
C:\Users\salmo\AppData\Local\Programs\Python\Python311\python.exe answer_with_context.py "How does CoachX help with workout planning?"
```

## Expected Output

The query script prints step-by-step progress, embedding dimensions, and the top matching chunks:

```text
[1/4] Loading configuration...
[2/4] Embedding query with Ollama model 'nomic-embed-text'...
[3/4] Searching Pinecone index 'example-chunks'...
[4/4] Search complete.
```

The grounded answer script prints five progress steps, a grounded answer, and source chunks:

```text
[1/5] Loading configuration...
[2/5] Embedding question with 'nomic-embed-text'...
[3/5] Retrieving top 3 chunks from Pinecone...
[4/5] Sending question and chunks to GPT-OSS...
[5/5] Grounded answer:
```

## Useful Checks

Check local embeddings:

```powershell
C:\Users\salmo\AppData\Local\Programs\Python\Python311\python.exe ollama_embed_texts.py
```

Check Ollama cloud chat models:

```powershell
C:\Users\salmo\AppData\Local\Programs\Python\Python311\python.exe ollama_chat_model_check.py
```

Check Python syntax:

```powershell
C:\Users\salmo\AppData\Local\Programs\Python\Python311\python.exe -m py_compile upload_to_pinecone.py query_pinecone.py answer_with_context.py
```

## Notes

- The Pinecone index must use `768` dimensions because `nomic-embed-text` returns 768-dimensional vectors.
- `PINECONE_NAMESPACE` defaults to `coachx-sample`.
- `PINECONE_TOP_K` defaults to `3`.
- `OLLAMA_CHAT_MODEL` defaults to `gpt-oss:20b-cloud`; switch to `gpt-oss:120b-cloud` in `.env` if desired.
