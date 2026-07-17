import importlib
from typing import Any, Awaitable, Optional, cast

from psycopg_pool import AsyncConnectionPool
from langchain_postgres import PGVector
from langchain_ollama import OllamaEmbeddings
from config import settings

_pool: Optional[AsyncConnectionPool] = None
_checkpointer: Any = None
_vector_store: Optional[PGVector] = None


async def get_pool() -> AsyncConnectionPool:
    global _pool
    if _pool is None:
        _pool = AsyncConnectionPool(
            conninfo=settings.DATABASE_URL,
            open=False,
            kwargs={"autocommit": True},
        )
        await cast(Awaitable[None], _pool.open())
    assert _pool is not None
    return _pool


async def get_checkpointer() -> Any:
    global _checkpointer
    if _checkpointer is None:
        module = importlib.import_module("langgraph.checkpoint.postgres.aio")
        checkpointer_cls = getattr(module, "AsyncPostgresSaver")
        pool = await cast(Awaitable[AsyncConnectionPool], get_pool())
        _checkpointer = checkpointer_cls(pool)
        await _checkpointer.setup()
    return _checkpointer


async def get_vector_store() -> PGVector:
    global _vector_store
    if _vector_store is None:
        # Keep this function async for consistency with node/workflow call sites.
        await cast(Awaitable[AsyncConnectionPool], get_pool())
        embeddings = OllamaEmbeddings(
            model=settings.OLLAMA_EMBED_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
        )
        store = PGVector(
            embeddings=embeddings,
            collection_name="career_knowledge",
            connection=_async_connection_string(settings.DATABASE_URL),
            use_jsonb=True,
            async_mode=True,
        )
        # In async_mode the constructor defers DB setup; initialise the
        # extension, tables and collection before first use.
        await cast(Awaitable[None], store.__apost_init__())
        _vector_store = store
    assert _vector_store is not None
    return _vector_store


def _async_connection_string(url: str) -> str:
    """Ensure the SQLAlchemy URL uses the async psycopg driver.

    PGVector(async_mode=True) needs a driver-qualified URL such as
    postgresql+psycopg://...; a bare postgresql:// URL defaults to psycopg2.
    """
    if url.startswith("postgresql+"):
        return url
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    return url
