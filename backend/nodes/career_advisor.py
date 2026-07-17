from typing import Any, Optional, Protocol, cast

from langchain_core.documents import Document
from llm import ainvoke_text, build_llm
from state.sandbox_state import SandboxState
from database.connection import get_vector_store


class SupportsAsyncSimilaritySearch(Protocol):
    async def asimilarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> list[Document]: ...


llm = build_llm(temperature=0.3, num_predict=3072)

_SYSTEM = """You are a strategic career advisor combining the perspective of an executive recruiter and a data-driven market analyst.

Your task: answer the candidate's career question with specific, actionable, evidence-based guidance.

Rules:
- Ground your advice in the two sources provided: (1) the knowledge-base context and (2) the candidate's resume. When the resume is present, tailor everything to their actual experience, skills, seniority, and gaps rather than giving generic advice.
- If the knowledge-base context is empty or says no data is available, rely on well-established, current industry knowledge and say so briefly rather than fabricating statistics.
- Do NOT invent specific numbers, salaries, employers, or the candidate's history. If you cite a metric, keep it clearly directional, not fabricated precision.
- Be concrete: name specific skills, roles, technologies, and next steps rather than platitudes.
- Match the candidate's level. Do not suggest entry-level advice to a senior candidate or vice versa.
- Keep it focused and skimmable; avoid filler and repetition.

Respond with ONLY the following Markdown structure, no preamble:

## Direct Answer
[clear, direct response tailored to the candidate]

## Market Trends
- [relevant, current trend tied to the candidate's field]

## Skill Gaps to Address
- [specific skill or experience the candidate should build, given their resume and the query]

## Actionable Next Steps
1. [concrete action]
2. [concrete action]
3. [concrete action]
"""


async def career_advisor_node(state: SandboxState) -> dict[str, str]:
    vector_store = cast(SupportsAsyncSimilaritySearch, await get_vector_store())
    docs: list[Document] = await vector_store.asimilarity_search(state["query"], k=4)
    context = "\n\n".join(doc.page_content for doc in docs) if docs else "No specific market data available."

    resume = state.get("resume", "").strip()
    resume_section = (
        f"Candidate's Resume:\n{resume}\n\n"
        if resume
        else "Candidate's Resume:\n(Not provided.)\n\n"
    )

    user_content = (
        f"Relevant context from knowledge base:\n{context}\n\n"
        f"{resume_section}"
        f"Career Query:\n{state['query']}"
    )
    text = await ainvoke_text(llm, _SYSTEM, user_content)
    return {"advice": text}
