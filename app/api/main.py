
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request, HTTPException
from ollama import RequestError, ResponseError
from pydantic import BaseModel, Field

from app.rag import RAG
from app.config import TOP_K

logger = logging.getLogger(__name__)

# 1. Define request model
class AskRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=TOP_K, ge=1, le=10)


# 2. Define response models
class SourceItem(BaseModel):
    source: str | None = None
    page: int | None = None
    chunk: int | None = None
    score: float | None = None
    selected: bool = False


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceItem] = Field(default_factory=list)


# 3. Initialize RAG when the server starts
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.rag = RAG()
    yield


app = FastAPI(
    title="Enterprise RAG API",
    description="API for the Enterprise RAG application",
    version="1.0.0",
    lifespan=lifespan,
)


# 4. Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}


# 5. Ask endpoint
@app.post("/ask", response_model=AskResponse)
def ask_question(payload: AskRequest, request: Request):

    rag = request.app.state.rag

    try:
        answer, source_result = rag.ask(
            payload.query,
            top_k=payload.top_k
        )

    except RequestError as exc:
        logger.exception("Failed to connect to Ollama")

        raise HTTPException(
            status_code=503,
            detail="LLM service is unavailable. Please try again later."
        ) from exc

    except ResponseError as exc:
        logger.exception("Ollama returned an error")

        raise HTTPException(
            status_code=502,
            detail="LLM service returned an error. Please try again later."
        ) from exc

    sources = []

    if source_result:
        context_results = (
            source_result.get("context_results")
            or [source_result]
        )

        for i, item in enumerate(context_results):
            metadata = item.get("metadata") or {}

            sources.append(
                SourceItem(
                    source=metadata.get("source"),
                    page=metadata.get("page"),
                    chunk=metadata.get("chunk"),
                    score=item.get("score"),
                    selected=(i == 0),
                )
            )

    return AskResponse(
        answer=answer,
        sources=sources
    )
