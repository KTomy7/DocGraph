"""
DocGraph - Knowledge Graph Engine (LightRAG)
Manages entity extraction, relationship mapping, and multi-hop reasoning.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from lightrag import LightRAG, QueryParam
from lightrag.llm.ollama import ollama_model_complete, ollama_embed
from lightrag.utils import EmbeddingFunc

from src.config import RAG_DIR, LLM_MODEL, EMBEDDING_MODEL, OLLAMA_HOST

logger = logging.getLogger(__name__)


def _run_async_safely(awaitable):
    """Run a coroutine without tripping over an already-running event loop."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(asyncio.run, awaitable)
        return future.result()


def get_rag_instance() -> LightRAG:
    """Initialize LightRAG with local Ollama endpoints."""
    RAG_DIR.mkdir(parents=True, exist_ok=True)

    async def local_embedding(texts: list[str]) -> list[list[float]]:
        return await ollama_embed.func(
            texts=texts,
            embed_model=EMBEDDING_MODEL,
            host=OLLAMA_HOST,
        )

    async def local_llm(
        prompt: str,
        system_prompt: Optional[str] = None,
        history_messages: Optional[list] = None,
        **kwargs,
    ) -> str:
        if history_messages is None:
            history_messages = []

        # LightRAG supplies the model through hashing_kv.global_config.
        # Remove the legacy model key so it cannot conflict with that config.
        kwargs.pop("model", None)

        return await ollama_model_complete(
            prompt,
            system_prompt,
            history_messages,
            host=OLLAMA_HOST,
            **kwargs,
        )

    return LightRAG(
        working_dir=str(RAG_DIR),
        llm_model_func=local_llm,
        embedding_func=EmbeddingFunc(
            embedding_dim=768,  # nomic-embed-text dimension
            max_token_size=8192,
            func=local_embedding,
        ),
        llm_model_name=LLM_MODEL,
    )


async def index_document_async(text: str, canonical_filename: str) -> None:
    """Insert document text into the graph without assuming a sync caller."""
    if not text.strip():
        return

    rag = get_rag_instance()
    payload = f"Source Document: {canonical_filename}\n\n{text}"

    if hasattr(rag, "initialize_storages"):
        await rag.initialize_storages()

    if hasattr(rag, "ainsert"):
        await rag.ainsert(payload)
        return

    await asyncio.to_thread(rag.insert, payload)


def index_document(text: str, canonical_filename: str) -> None:
    """Insert document text into the LightRAG knowledge graph."""
    _run_async_safely(index_document_async(text, canonical_filename))


async def query_graph_async(query: str, mode: str = "hybrid") -> str:
    """Query the graph using the async LightRAG interface."""
    rag = get_rag_instance()
    param = QueryParam(mode=mode)

    if hasattr(rag, "initialize_storages"):
        await rag.initialize_storages()

    if hasattr(rag, "aquery"):
        return await rag.aquery(query, param=param)

    return await asyncio.to_thread(rag.query, query, param=param)


def query_graph(query: str, mode: str = "hybrid") -> str:
    """
    Query the knowledge graph.
    Modes: 'hybrid' (entities + vectors), 'local' (entities only), 'global' (community summaries).
    """
    return _run_async_safely(query_graph_async(query, mode=mode))
