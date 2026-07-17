from uuid import uuid4
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from resume import load_resume
from workflows.mock_interview import get_interview_graph

router = APIRouter()


class InterviewTurn(BaseModel):
    thread_id: Optional[str] = None
    message: str = ""
    jd_text: str = ""


@router.post("/mock-interview")
async def mock_interview(body: InterviewTurn):
    graph = await get_interview_graph()

    if body.thread_id:
        # Continuing an existing interview: the message is required.
        if not body.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty.")
        thread_id = body.thread_id
        state_input = {"messages": [HumanMessage(content=body.message)]}
    else:
        # Starting a new interview: seed JD + resume, let the model open.
        thread_id = str(uuid4())
        try:
            resume = await load_resume()
        except (ValueError, FileNotFoundError):
            resume = ""
        state_input = {"messages": [], "jd": body.jd_text, "resume": resume}

    config = {"configurable": {"thread_id": thread_id}}
    result = await graph.ainvoke(state_input, config=config)

    reply = result["messages"][-1].content
    return {"thread_id": thread_id, "reply": reply}
