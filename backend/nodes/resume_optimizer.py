from typing import TypedDict, cast

from llm import ainvoke_json, ainvoke_text, build_llm
from state.application_state import ApplicationState

llm = build_llm(temperature=0.1, num_predict=4096)
score_llm = build_llm(temperature=0.0, num_predict=256, json_mode=True)

_SCORE_SYSTEM = """You extract a single numeric match score from a resume-vs-JD critique.

Read the critique and return the overall match score it states, as JSON only:
{"match_score": <integer 0-100>}

Rules:
- Use the exact score the critique reports in its "Match Score" section.
- If no explicit score is present, estimate it from the critique's strengths and gaps.
- match_score must be an integer between 0 and 100."""

_SYSTEM = """You are an expert resume coach and former FAANG hiring manager who has reviewed thousands of resumes and understands modern ATS ranking.

Your task: critique the candidate's resume against the job description analysis AND hand the candidate exact, copy-paste-ready resume content. The most valuable part of your output is telling them precisely what to write and where to put it — not vague advice.

Rules:
- Ground every point in evidence that actually appears in the resume or the JD analysis. Do NOT invent employers, job titles, dates, or fabricate specific metrics the candidate never mentioned.
- When a bullet needs a number the candidate hasn't given, insert a clearly-marked placeholder like "[X%]", "[N users]", or "[$Y]" so they can fill it in — never make up a figure and present it as fact.
- Every suggestion must be concrete and directly usable. "Add cloud experience" is useless; a fully-written bullet the candidate can paste is what you deliver.
- Prefer quantified, results-oriented phrasing: strong action verb + what you did + technology/scope + measurable outcome.
- The Match Score must be justified by concrete alignment and gaps, not a gut feeling. Score using this rubric and sum the bands:
  - Required-skills coverage (0-40): fraction of the JD's required skills clearly evidenced in the resume, scaled to 40.
  - Relevant experience & seniority match (0-25): does the depth, scope, and years align with the role's level?
  - Quantified impact & achievements (0-15): are accomplishments backed by concrete, measurable results?
  - Nice-to-have / differentiators (0-10): coverage of preferred skills and standout strengths.
  - ATS keyword & phrasing alignment (0-10): does the resume mirror the JD's terminology?
  Calibrate honestly: a strong-but-imperfect fit lands ~70-85; reserve 90+ for near-perfect matches.
- For ATS Keywords, list only terms that appear in the JD's Required/Nice-to-Have skills but are missing (or under-represented) in the resume. Do not pad the list.

Respond with ONLY the following Markdown structure, no preamble:

## Match Score
[0-100]/100 — [one-line justification citing the rubric bands that drove the score]

## Strengths
- [specific resume evidence that aligns with a specific JD requirement]

## Critical Gaps
- [specific JD requirement that is missing or weak in the resume, and why it matters to this role]

## Rewrite These Bullets
For each weak bullet that already exists in the resume:
- **Section:** [which job/section it lives in]
  - **Current:** "[the exact existing bullet, quoted from the resume]"
  - **Rewrite:** "[the improved, ready-to-paste version with a stronger verb, the JD's keywords, and a [placeholder] for any missing metric]"
  - **Why:** [the specific JD requirement or ATS keyword this now targets]

## Add These Bullets
New, ready-to-paste bullets that fill a gap the JD requires but the resume lacks. Only propose bullets the candidate could plausibly claim from their existing background — mark any assumption in [brackets]:
- **Add to [section]:** "[fully-written bullet with action verb, JD keyword, and [placeholder] metric]" — covers [JD requirement].

## ATS Keywords to Add
[comma-separated keywords from the JD that are missing in the resume]
"""


class ResumeOptimizerInput(TypedDict):
    structured_jd: str
    master_resume: str


async def resume_optimizer_node(state: ApplicationState) -> dict[str, object]:
    if "structured_jd" not in state or "master_resume" not in state:
        raise KeyError("Missing required keys for resume optimizer: structured_jd, master_resume")

    optimizer_state = cast(ResumeOptimizerInput, state)
    user_content = (
        f"Job Description Analysis:\n{optimizer_state['structured_jd']}\n\n"
        f"Candidate's Resume:\n{optimizer_state['master_resume']}"
    )
    text = await ainvoke_text(llm, _SYSTEM, user_content)

    # Structured-mode extraction: robustly pull the numeric score as JSON instead
    # of regex-parsing prose, so the UI always gets a reliable 0-100 integer.
    score = await _extract_score(text)
    return {"critique": text, "match_score": score}


async def _extract_score(critique: str) -> int:
    data = await ainvoke_json(score_llm, _SCORE_SYSTEM, f"Critique:\n{critique}")
    raw = data.get("match_score")
    try:
        value = int(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return -1  # unknown; the UI falls back to markdown parsing
    return max(0, min(100, value))
