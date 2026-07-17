from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from resume import load_resume
from api.sse import sse_response
from nodes.cover_letter import generate_cover_letter, stream_cover_letter

router = APIRouter()


class CoverLetterRequest(BaseModel):
    jd_text: str = ""
    tone: str = ""
    extra: str = ""


async def _resume_or_empty() -> str:
    try:
        return await load_resume()
    except (ValueError, FileNotFoundError):
        return ""


@router.post("/cover-letter")
async def cover_letter(body: CoverLetterRequest):
    if not body.jd_text.strip():
        raise HTTPException(status_code=400, detail="Provide the job description text.")

    result = await generate_cover_letter(body.jd_text, await _resume_or_empty(), body.tone, body.extra)
    return {"result": result}


@router.post("/cover-letter/stream")
async def cover_letter_stream(body: CoverLetterRequest):
    if not body.jd_text.strip():
        raise HTTPException(status_code=400, detail="Provide the job description text.")

    return sse_response(
        stream_cover_letter(body.jd_text, await _resume_or_empty(), body.tone, body.extra)
    )
