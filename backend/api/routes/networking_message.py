from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from resume import load_resume
from api.sse import sse_response
from nodes.networking_message import stream_networking_message, write_networking_message

router = APIRouter()


class NetworkingRequest(BaseModel):
    recipient: str = ""
    platform: str = ""
    company: str = ""
    role: str = ""
    context: str = ""


def _resume_or_empty() -> str:
    try:
        return load_resume()
    except FileNotFoundError:
        return ""


@router.post("/networking-message")
async def networking_message(body: NetworkingRequest):
    if not body.context.strip() and not body.company.strip():
        raise HTTPException(status_code=400, detail="Provide some context or a target company.")

    result = await write_networking_message(
        body.recipient, body.platform, body.company, body.role, body.context, _resume_or_empty()
    )
    return {"result": result}


@router.post("/networking-message/stream")
async def networking_message_stream(body: NetworkingRequest):
    if not body.context.strip() and not body.company.strip():
        raise HTTPException(status_code=400, detail="Provide some context or a target company.")

    return sse_response(
        stream_networking_message(
            body.recipient, body.platform, body.company, body.role, body.context, _resume_or_empty()
        )
    )
