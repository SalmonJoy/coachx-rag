from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from backend.app.services.chat import grounded_chat
from backend.app.services.pinecone_viewer import list_chunks, list_index_names, list_namespaces
from backend.app.services.pdf_ingestion import ingest_pdf_upload


router = APIRouter()


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    index_name: str = Field(..., min_length=1)
    namespace: str | None = None
    top_k: int | None = Field(default=3, gt=0)


class ChatChunk(BaseModel):
    id: str
    score: float
    text: str


class ChatResponse(BaseModel):
    status: str
    query: str
    answer: str
    index_name: str
    namespace: str
    top_k: int
    chunks: list[ChatChunk]


class PineconeNamespace(BaseModel):
    name: str
    vector_count: int


class PineconeIndexesResponse(BaseModel):
    status: str
    indexes: list[str]


class PineconeNamespacesResponse(BaseModel):
    status: str
    index_name: str
    namespaces: list[PineconeNamespace]


class PineconeChunk(BaseModel):
    id: str
    text: str
    heading: str
    source_file: str
    start_line: int | str
    end_line: int | str
    embedding_model: str


class PineconeChunksResponse(BaseModel):
    status: str
    index_name: str
    namespace: str
    count: int
    chunks: list[PineconeChunk]


@router.get("/")
def read_root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "ok",
    }


@router.get("/health")
def read_health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/pinecone/indexes", response_model=PineconeIndexesResponse)
def pinecone_indexes() -> dict[str, object]:
    try:
        return {"status": "ok", "indexes": list_index_names()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/pinecone/namespaces", response_model=PineconeNamespacesResponse)
def pinecone_namespaces(index_name: str = Query(..., min_length=1)) -> dict[str, object]:
    try:
        index_name = index_name.strip()
        if not index_name:
            raise ValueError("Pinecone index name is required")
        return {
            "status": "ok",
            "index_name": index_name,
            "namespaces": list_namespaces(index_name),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/pinecone/chunks", response_model=PineconeChunksResponse)
def pinecone_chunks(
    index_name: str = Query(..., min_length=1),
    namespace: str = Query(..., min_length=1),
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, object]:
    try:
        index_name = index_name.strip()
        namespace = namespace.strip()
        chunks = list_chunks(index_name, namespace, limit)
        return {
            "status": "ok",
            "index_name": index_name,
            "namespace": namespace,
            "count": len(chunks),
            "chunks": chunks,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/ingest/pdf")
async def ingest_pdf(
    file: UploadFile = File(...),
    index_name: str = Form(...),
    namespace: str | None = Form(None),
) -> dict[str, object]:
    try:
        return await ingest_pdf_upload(file, index_name, namespace)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> dict[str, object]:
    try:
        return grounded_chat(
            request.query,
            request.index_name,
            request.namespace,
            request.top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    
