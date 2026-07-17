import base64
from uuid import uuid4
from typing import Annotated, Optional, Union

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from resume import load_resume
from workflows.core_application import get_core_graph

router = APIRouter()


@router.post(
    "/analyze-job",
    responses={
        400: {"description": "Neither jd_text nor jd_image was provided"},
        500: {"description": "Resume file not found in data/"},
    },
)
async def analyze_job(
    jd_text: Annotated[Optional[str], Form()] = None,
    jd_image: Annotated[Optional[UploadFile], File()] = None,
):
    if not jd_text and not jd_image:
        raise HTTPException(status_code=400, detail="Provide either jd_text or jd_image.")

    try:
        master_resume = load_resume()
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))

    raw_jd: Union[str, dict[str, str]]
    if jd_image:
        contents = await jd_image.read()
        b64 = base64.b64encode(contents).decode()
        media_type = jd_image.content_type or "application/octet-stream"
        raw_jd = {"type": "image", "data": b64, "media_type": media_type}
    else:
        raw_jd = jd_text or ""

    graph = await get_core_graph()
    config = {"configurable": {"thread_id": str(uuid4())}}

    result = await graph.ainvoke(
        {"raw_jd": raw_jd, "master_resume": master_resume},
        config=config,
    )

    return {
        "structured_jd": result["structured_jd"],
        "critique": result["critique"],
        "match_score": result.get("match_score", -1),
        "prep": result["prep"],
    }
