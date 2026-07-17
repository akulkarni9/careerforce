from typing import Any, AsyncIterator, Optional, Protocol, cast

from langchain_core.documents import Document

from llm import ainvoke_text, astream_text, build_llm
from database.connection import get_vector_store


class SupportsAsyncSimilaritySearch(Protocol):
    async def asimilarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> list[Document]: ...


llm = build_llm(temperature=0.3, num_predict=4096)

_SYSTEM = """You are a senior career coach and curriculum designer who builds realistic, week-by-week upskilling plans.

Your task: given the candidate's current resume, a target role (and optionally a specific job description) and market context, produce a focused learning plan that closes the highest-leverage gaps.

Rules:
- Anchor the plan in the DELTA between the candidate's current skills/experience and what the target role requires. Do not re-teach what they already know.
- Prioritize ruthlessly: focus on the few gaps that most change their candidacy, not an exhaustive list.
- Every week must have concrete, verifiable outputs (a project artifact, a repo, a certification, a written piece) - not just "read about X".
- Recommend specific, credible resource TYPES and well-known options, but do not fabricate exact course titles, URLs, prices, or instructors.
- Match scope to the candidate's seniority and the size of the gap. Keep the plan achievable alongside a job or job search.
- Ground market claims in the provided knowledge-base context; if it is empty, rely on established industry knowledge and say so briefly.

Respond with ONLY the following Markdown structure, no preamble:

## Target & Current Fit
[2-3 sentences: where the candidate stands vs the target role, and the core gap]

## Priority Gaps
1. [gap] - why it matters for this role
2. [gap] - why it matters
3. [gap] - why it matters

## Week-by-Week Plan
- **Week 1:** focus - concrete output
- **Week 2:** focus - concrete output
- **Week 3:** focus - concrete output
- **Week 4:** focus - concrete output
(extend to 6-8 weeks if the gap is large)

## Portfolio Proof
- [what to build/publish so the new skills are visible to recruiters]

## How To Signal It
- [resume line, LinkedIn, or interview talking point that reflects the new skills]
"""


async def _build_user_content(target_role: str, jd: str, resume: str) -> str:
    query = f"{target_role} required skills, market demand, hiring trends"
    vector_store = cast(SupportsAsyncSimilaritySearch, await get_vector_store())
    docs: list[Document] = await vector_store.asimilarity_search(query, k=4)
    context = "\n\n".join(d.page_content for d in docs) if docs else "No specific market data available."

    return (
        f"Target role: {target_role.strip() or '(Not specified.)'}\n\n"
        f"Target job description (if provided):\n{jd.strip() or '(Not provided.)'}\n\n"
        f"Market context from knowledge base:\n{context}\n\n"
        f"Candidate's Resume:\n{resume or '(Not provided.)'}\n"
    )


async def build_skill_gap_plan(target_role: str, jd: str, resume: str) -> str:
    user_content = await _build_user_content(target_role, jd, resume)
    return await ainvoke_text(llm, _SYSTEM, user_content)


async def stream_skill_gap_plan(target_role: str, jd: str, resume: str) -> AsyncIterator[str]:
    """Run RAG retrieval, then yield the plan token-by-token for SSE streaming."""
    user_content = await _build_user_content(target_role, jd, resume)
    async for chunk in astream_text(llm, _SYSTEM, user_content):
        yield chunk
