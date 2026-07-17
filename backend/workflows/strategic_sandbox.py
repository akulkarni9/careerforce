from langgraph.graph import StateGraph, END
from state.sandbox_state import SandboxState
from nodes.career_advisor import career_advisor_node

_graph = None


async def get_sandbox_graph():
    global _graph
    if _graph is None:
        from database.connection import get_checkpointer
        checkpointer = await get_checkpointer()

        workflow = StateGraph(SandboxState)
        workflow.add_node("career_advisor", career_advisor_node)

        workflow.set_entry_point("career_advisor")
        workflow.add_edge("career_advisor", END)

        _graph = workflow.compile(checkpointer=checkpointer)
    return _graph
