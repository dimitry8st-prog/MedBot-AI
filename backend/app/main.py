"""
MedBot AI — FastAPI application (Stage 2: RAG + GigaChat)
"""

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.rag_engine import get_rag_engine
from app.services.ask_service import DISCLAIMER, ask
from app.services.gigachat_client import GigaChatError

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-платформа для медицинских специалистов (RAG + GigaChat)",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, examples=["лечение артериальной гипертензии"])
    specialty: Optional[str] = Field(None, examples=["cardiology"])
    top_k: Optional[int] = Field(None, ge=1, le=20)
    source_filter: Optional[str] = Field(None, examples=["minzdrav"])


class SearchHit(BaseModel):
    chunk_id: str
    text: str
    score: float
    base_similarity: float
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    query: str
    results: List[SearchHit]
    disclaimer: str


class AskRequest(BaseModel):
    query: str = Field(..., min_length=2, examples=["Какая первая линия терапии АГ?"])
    specialty: Optional[str] = Field(None, examples=["cardiology"])


class AskResponse(BaseModel):
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    disclaimer: str
    source_origin: str = "rag"
    source_label: str = ""


@app.get("/api/v1/health")
def health() -> Dict[str, Any]:
    """Health check"""
    rag = get_rag_engine()
    stats = rag.chroma_client.get_collection_stats(settings.CHROMADB_COLLECTION_NAME)
    gigachat_configured = bool(
        settings.GIGACHAT_API_KEY and not settings.GIGACHAT_API_KEY.startswith("your_")
    )
    tg_configured = bool(
        settings.TG_BOT_TOKEN and not settings.TG_BOT_TOKEN.startswith("your_")
    )
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "env": settings.APP_ENV,
        "collection": settings.CHROMADB_COLLECTION_NAME,
        "documents": stats.get("count", 0),
        "gigachat_configured": gigachat_configured,
        "telegram_configured": tg_configured,
    }


@app.post("/api/v1/search", response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    """RAG semantic search по клиническим документам"""
    try:
        rag = get_rag_engine()
        results = rag.search(
            query=request.query,
            specialty=request.specialty,
            top_k=request.top_k,
            source_filter=request.source_filter,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}") from exc

    return SearchResponse(
        query=request.query,
        results=[
            SearchHit(
                chunk_id=r.chunk_id,
                text=r.text,
                score=r.score,
                base_similarity=r.base_similarity,
                metadata=r.metadata,
            )
            for r in results
        ],
        disclaimer=DISCLAIMER,
    )


@app.post("/api/v1/ask", response_model=AskResponse)
def ask_endpoint(request: AskRequest) -> AskResponse:
    """RAG + GigaChat: ответ на вопрос врача"""
    try:
        result = ask(query=request.query, specialty=request.specialty)
    except GigaChatError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ask failed: {exc}") from exc

    return AskResponse(
        query=result.query,
        answer=result.answer,
        sources=result.sources,
        disclaimer=result.disclaimer,
        source_origin=result.source_origin,
        source_label=result.source_label,
    )


@app.get("/")
def root() -> Dict[str, str]:
    return {
        "message": f"{settings.APP_NAME} API",
        "docs": "/docs",
        "health": "/api/v1/health",
        "ask": "/api/v1/ask",
    }
