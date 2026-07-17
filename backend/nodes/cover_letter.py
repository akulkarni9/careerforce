from llm import ainvoke_refine, astream_refine, build_llm

llm = build_llm(temperature=0.4, num_predict=4096)

_CRITIC_FOCUS = """- Every claim must map to a real accomplishment in the resume; cut anything generic or unsupported.
- The opening hook must be specific, not a template line.
- Mirror the JD's key terminology naturally for ATS, without keyword-stuffing.
- Tighten wording, remove cliches and filler, and keep it within the requested length.
- Lead with the strongest, most role-relevant match."""

_SYSTEM = """You are an expert career writer who produces tailored, high-converting cover letters that hiring managers actually read.

Your task: write a cover letter for THIS candidate applying to THIS role, drawing only on the resume and job description provided.

Rules:
- Ground every claim in the candidate's actual resume. Never invent employers, titles, dates, metrics, or skills they do not have.
- Map the candidate's real accomplishments to the specific requirements in the job description. Lead with the strongest, most relevant matches.
- Mirror important keywords and terminology from the job description naturally (helps with ATS and recruiter skim), without keyword-stuffing.
- Sound like a competent human, not a template. No cliches ("I am writing to express my interest", "team player", "hit the ground running"). Open with a specific hook.
- Respect the requested tone and length. Default to ~250-350 words, 3-4 tight paragraphs.
- If the company or role name is unknown, use a natural, non-awkward phrasing rather than leaving bracketed placeholders.

Respond with ONLY the following Markdown structure, no preamble:

## Cover Letter
[the full letter, ready to send: greeting, body paragraphs, and a confident closing with the candidate's name]

## Why This Works
- [1-line note on the strongest match you led with]
- [1-line note on the keyword/requirement alignment]
"""


async def generate_cover_letter(jd: str, resume: str, tone: str, extra: str) -> str:
    return await ainvoke_refine(llm, _SYSTEM, _user_content(jd, resume, tone, extra), _CRITIC_FOCUS)


def stream_cover_letter(jd: str, resume: str, tone: str, extra: str):
    """Stream the refined cover letter token-by-token for SSE."""
    return astream_refine(llm, _SYSTEM, _user_content(jd, resume, tone, extra), _CRITIC_FOCUS)


def _user_content(jd: str, resume: str, tone: str, extra: str) -> str:
    tone_line = tone.strip() or "professional and confident"
    extra_section = f"\nExtra emphasis requested by the candidate:\n{extra.strip()}\n" if extra.strip() else ""
    return (
        f"Requested tone: {tone_line}\n\n"
        f"Candidate's Resume:\n{resume or '(Not provided.)'}\n\n"
        f"Job Description:\n{jd or '(Not provided.)'}\n"
        f"{extra_section}"
    )
