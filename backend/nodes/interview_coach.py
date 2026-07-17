from typing import TypedDict, cast

from llm import ainvoke_text, build_llm
from state.application_state import ApplicationState

llm = build_llm(temperature=0.2, num_predict=3072)

_SYSTEM = """You are an expert interview coach who has prepared hundreds of candidates for technical and leadership interviews at top companies.

Your task: using the job description analysis and the resume critique provided, prepare the candidate for THIS specific interview.

Rules:
- Tailor every question and talking point to the actual role requirements and the candidate's real background as reflected in the inputs. Do NOT invent experience the candidate does not have.
- Questions must be realistic for the role's level and domain (mix behavioural and role-specific/technical as appropriate).
- In the STAR guidance, suggest how the candidate can frame their genuine experience; use placeholders like "[your project]" rather than fabricating specifics or numbers.
- Address the weaknesses surfaced in the resume critique directly under Red Flags, with concrete reframing strategies.
- Keep advice practical and concise; no filler.

Respond with ONLY the following Markdown structure, no preamble:

## Top 5 Likely Interview Questions
For each question:
**Q: [question]**
- **Situation:** [suggested setup using the candidate's background]
- **Task:** [the challenge]
- **Action:** [specific actions to highlight]
- **Result:** [type of quantifiable result to aim for]

## Questions to Ask the Interviewer
1. [thoughtful, role-specific question]
2. [thoughtful, role-specific question]
3. [thoughtful, role-specific question]

## Red Flags to Address Proactively
- [a real concern from the critique + how to reframe it credibly]
"""


class InterviewCoachInput(TypedDict):
    structured_jd: str
    critique: str


async def interview_coach_node(state: ApplicationState) -> dict[str, str]:
    if "structured_jd" not in state or "critique" not in state:
        raise KeyError("Missing required keys for interview coach: structured_jd, critique")

    coach_state = cast(InterviewCoachInput, state)
    user_content = (
        f"Job Description Analysis:\n{coach_state['structured_jd']}\n\n"
        f"Resume Critique:\n{coach_state['critique']}"
    )
    text = await ainvoke_text(llm, _SYSTEM, user_content)
    return {"prep": text}
