from typing import Any

from langgraph.graph import StateGraph, END
from state.application_state import ApplicationState
from nodes.jd_analyser import jd_analyser_node
from nodes.resume_optimizer import resume_optimizer_node
from nodes.interview_coach import interview_coach_node

_graph: Any = None


async def get_core_graph() -> Any:
    global _graph
    if _graph is None:
        from database.connection import get_checkpointer
        checkpointer = await get_checkpointer()

        workflow: Any = StateGraph(ApplicationState)
        workflow.add_node("jd_analyser", jd_analyser_node)
        workflow.add_node("resume_optimizer", resume_optimizer_node)
        workflow.add_node("interview_coach", interview_coach_node)

        workflow.set_entry_point("jd_analyser")
        workflow.add_edge("jd_analyser", "resume_optimizer")
        workflow.add_edge("resume_optimizer", "interview_coach")
        workflow.add_edge("interview_coach", END)

        _graph = workflow.compile(checkpointer=checkpointer)
    return _graph
