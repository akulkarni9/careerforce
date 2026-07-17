from langgraph.graph import StateGraph, END

from state.interview_state import InterviewState
from nodes.mock_interviewer import mock_interviewer_node

_graph = None


async def get_interview_graph():
    global _graph
    if _graph is None:
        from database.connection import get_checkpointer
        checkpointer = await get_checkpointer()

        workflow = StateGraph(InterviewState)
        workflow.add_node("interviewer", mock_interviewer_node)

        workflow.set_entry_point("interviewer")
        workflow.add_edge("interviewer", END)

        _graph = workflow.compile(checkpointer=checkpointer)
    return _graph
