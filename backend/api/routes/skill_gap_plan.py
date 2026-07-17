from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from resume import load_resume
from api.sse import sse_response
from nodes.skill_gap_plan import build_skill_gap_plan, stream_skill_gap_plan

router = APIRouter()


class SkillGapRequest(BaseModel):
    target_role: str = ""
    jd_text: str = ""


async def _resume_or_empty() -> str:
    try:
        return await load_resume()
    except (ValueError, FileNotFoundError):
        return ""


@router.post("/skill-gap-plan")
async def skill_gap_plan(body: SkillGapRequest):
    if not body.target_role.strip() and not body.jd_text.strip():
        raise HTTPException(status_code=400, detail="Provide a target role or a job description.")

    result = await build_skill_gap_plan(body.target_role, body.jd_text, await _resume_or_empty())
    return {"result": result}


@router.post("/skill-gap-plan/stream")
async def skill_gap_plan_stream(body: SkillGapRequest):
    if not body.target_role.strip() and not body.jd_text.strip():
        raise HTTPException(status_code=400, detail="Provide a target role or a job description.")

    return sse_response(stream_skill_gap_plan(body.target_role, body.jd_text, await _resume_or_empty()))
