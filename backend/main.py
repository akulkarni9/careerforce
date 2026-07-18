from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.analyze_job import router as analyze_router
from api.routes.career_advice import router as career_router
from api.routes.resume_info import router as resume_router
from api.routes.cover_letter import router as cover_letter_router
from api.routes.company_research import router as company_research_router
from api.routes.networking_message import router as networking_router
from api.routes.skill_gap_plan import router as skill_gap_router
from api.routes.salary_negotiation import router as negotiation_router
from api.routes.mock_interview import router as interview_router
from database.connection import get_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_pool()
    from resume import setup_table
    await setup_table()
    yield
    from database.connection import _pool
    if _pool:
        await _pool.close()


app = FastAPI(title="CareerForge", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://careerforce.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router, prefix="/api")
app.include_router(career_router, prefix="/api")
app.include_router(resume_router, prefix="/api")
app.include_router(cover_letter_router, prefix="/api")
app.include_router(company_research_router, prefix="/api")
app.include_router(networking_router, prefix="/api")
app.include_router(skill_gap_router, prefix="/api")
app.include_router(negotiation_router, prefix="/api")
app.include_router(interview_router, prefix="/api")
