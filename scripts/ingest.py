"""
Ingest documents into the career knowledge vector store.

Usage:
    1. Add .txt or .md files to scripts/knowledge/
    2. Run: cd backend && python ../scripts/ingest.py

Each file becomes one or more chunks in the pgvector career_knowledge collection.
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from database.connection import get_vector_store

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


async def ingest():
    files = list(KNOWLEDGE_DIR.glob("*.txt")) + list(KNOWLEDGE_DIR.glob("*.md"))
    if not files:
        print(f"No .txt or .md files found in {KNOWLEDGE_DIR}")
        return

    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    docs = []

    for path in files:
        text = path.read_text(encoding="utf-8")
        chunks = splitter.split_text(text)
        for chunk in chunks:
            docs.append(Document(page_content=chunk, metadata={"source": path.name}))

    print(f"Ingesting {len(docs)} chunks from {len(files)} file(s)...")
    vector_store = await get_vector_store()
    await vector_store.aadd_documents(docs)
    print("Done.")


if __name__ == "__main__":
    asyncio.run(ingest())
