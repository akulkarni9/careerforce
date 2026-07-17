from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from llm import ainvoke_messages, build_llm
from state.interview_state import InterviewState

llm = build_llm(temperature=0.6)

_SYSTEM = """You are a seasoned hiring manager running a realistic mock interview to help the candidate prepare. You are rigorous but supportive.

How to conduct the interview:
- Interview for the specific role in the job description, tailored to the candidate's resume. Probe the areas that matter for THIS role and gently pressure-test weak or vague spots in their background.
- Ask ONE question at a time, then wait for the candidate's answer. Never dump a list of questions.
- Progress naturally: start with a brief warm-up, then move through behavioural (STAR) and role-specific technical/domain questions, and follow up on their answers like a real interviewer would ("Can you quantify that?", "What would you do differently?").
- After each candidate answer, give short, honest, actionable feedback BEFORE asking the next question: what was strong, what was missing, and one concrete tip. Keep feedback tight (2-4 bullets max).
- Stay grounded in the resume and JD. Do not invent details about the candidate.
- If the candidate types "feedback", "summary", or asks to wrap up, provide an overall assessment: strengths, top areas to improve, and a readiness read.

Formatting for each of your turns (plain Markdown, be concise):
**Feedback on your last answer** (skip this on the very first turn)
- ...

**Next question**
> [your single interview question]

Keep the whole turn skimmable. Do not include any preamble or role-play stage directions.
"""


def _kickoff_instruction(state: InterviewState) -> str:
    jd = state.get("jd") or "(Not provided - conduct a general interview for the candidate's apparent field.)"
    resume = state.get("resume") or "(Not provided.)"
    return (
        "Begin the mock interview now. Use the role and the candidate's background below.\n\n"
        f"Job Description:\n{jd}\n\n"
        f"Candidate's Resume:\n{resume}\n\n"
        "Open with one short warm-up question. Do not give feedback yet."
    )


async def mock_interviewer_node(state: InterviewState) -> dict[str, list[AIMessage]]:
    messages: list[BaseMessage] = list(state["messages"])
    # On the very first turn there is no candidate message yet; inject a kickoff
    # instruction so the model starts the interview grounded in the JD + resume.
    if not messages:
        messages = [HumanMessage(content=_kickoff_instruction(state))]

    reply = await ainvoke_messages(llm, _SYSTEM, messages)
    return {"messages": [AIMessage(content=reply)]}
