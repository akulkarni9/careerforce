from database.connection import get_pool

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS resumes (
    id INT PRIMARY KEY DEFAULT 1,
    filename TEXT NOT NULL,
    content TEXT NOT NULL,
    uploaded_at TIMESTAMPTZ DEFAULT now(),
    CHECK (id = 1)
);
"""


async def setup_table() -> None:
    pool = await get_pool()
    async with pool.connection() as conn:
        await conn.execute(_CREATE_TABLE)


async def load_resume() -> str:
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT content FROM resumes WHERE id = 1")
            row = await cur.fetchone()
    if not row:
        raise ValueError("No resume uploaded yet. Upload your resume first.")
    return row[0]


async def get_resume_info() -> dict:
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT filename FROM resumes WHERE id = 1")
            row = await cur.fetchone()
    if not row:
        return {"loaded": False, "filename": None}
    return {"loaded": True, "filename": row[0]}


async def save_resume(filename: str, content: str) -> None:
    pool = await get_pool()
    async with pool.connection() as conn:
        await conn.execute(
            """
            INSERT INTO resumes (id, filename, content)
            VALUES (1, %s, %s)
            ON CONFLICT (id) DO UPDATE
                SET filename = EXCLUDED.filename,
                    content  = EXCLUDED.content,
                    uploaded_at = now()
            """,
            (filename, content),
        )


def _extract_text(filename: str, data: bytes) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "pdf":
        from pypdf import PdfReader
        import io
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if ext == "docx":
        from docx import Document
        import io
        doc = Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs)
    raise ValueError(f"Unsupported file type: .{ext}")
