from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from resume import load_resume
from api.sse import sse_response
from nodes.salary_negotiation import coach_negotiation, stream_coach_negotiation

router = APIRouter()


class NegotiationRequest(BaseModel):
    role: str = ""
    offer: str = ""
    location: str = ""
    competing: str = ""


def _resume_or_empty() -> str:
    try:
        return load_resume()
    except FileNotFoundError:
        return ""


@router.post("/salary-negotiation")
async def salary_negotiation(body: NegotiationRequest):
    if not body.offer.strip():
        raise HTTPException(status_code=400, detail="Provide the offer details to negotiate.")

    result = await coach_negotiation(
        body.role, body.offer, body.location, body.competing, _resume_or_empty()
    )
    return {"result": result}


@router.post("/salary-negotiation/stream")
async def salary_negotiation_stream(body: NegotiationRequest):
    if not body.offer.strip():
        raise HTTPException(status_code=400, detail="Provide the offer details to negotiate.")

    return sse_response(
        stream_coach_negotiation(
            body.role, body.offer, body.location, body.competing, _resume_or_empty()
        )
    )
