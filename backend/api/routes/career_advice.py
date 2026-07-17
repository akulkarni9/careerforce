from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from resume import load_resume
from workflows.strategic_sandbox import get_sandbox_graph

router = APIRouter()


class CareerQuery(BaseModel):
    query: str


@router.post("/career-advice")
async def career_advice(body: CareerQuery):
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        resume = load_resume()
    except FileNotFoundError:
        resume = ""

    graph = await get_sandbox_graph()
    config = {"configurable": {"thread_id": str(uuid4())}}

    result = await graph.ainvoke({"query": body.query, "resume": resume}, config=config)

    return {"advice": result["advice"]}
