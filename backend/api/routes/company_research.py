from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.sse import sse_response
from nodes.company_research import research_company, stream_company_research

router = APIRouter()


class CompanyResearchRequest(BaseModel):
    company: str = ""
    role: str = ""
    jd_text: str = ""


@router.post("/company-research")
async def company_research(body: CompanyResearchRequest):
    if not body.company.strip() and not body.jd_text.strip():
        raise HTTPException(status_code=400, detail="Provide a company name or a job description.")

    result = await research_company(body.company, body.role, body.jd_text)
    return {"result": result}


@router.post("/company-research/stream")
async def company_research_stream(body: CompanyResearchRequest):
    if not body.company.strip() and not body.jd_text.strip():
        raise HTTPException(status_code=400, detail="Provide a company name or a job description.")

    return sse_response(stream_company_research(body.company, body.role, body.jd_text))
