from llm import ainvoke_text, astream_text, build_llm

llm = build_llm(temperature=0.5)

_SYSTEM = """You are a networking coach who writes short, human, effective outreach messages that get replies.

Your task: write outreach message(s) for the given scenario, grounded in the candidate's real background.

Rules:
- Match the recipient type, platform, and context. A LinkedIn connection note is <=300 characters; a cold recruiter message or referral ask is a few short sentences; email can be slightly longer with a subject line.
- Be specific and genuine. Reference a concrete reason for reaching out and a concrete, relevant detail from the candidate's background. Never generic flattery.
- Respect the reader's time: lead with the ask or the hook, keep it skimmable, make the next step effortless.
- Ground any claim about the candidate in their resume. Do not invent shared connections, past interactions, or experience.
- No cliches, no desperation, no over-formality. Sound like a sharp, friendly professional.

Respond with ONLY the following Markdown structure, no preamble:

## Message
[the primary ready-to-send message; include a **Subject:** line first if the platform is email]

## Shorter Variant
[a tighter alternative, e.g. a connection-note-length version]

## Follow-up (if no reply)
[a brief, polite nudge to send after ~1 week]
"""


async def write_networking_message(
    recipient: str, platform: str, company: str, role: str, context: str, resume: str
) -> str:
    content = _user_content(recipient, platform, company, role, context, resume)
    return await ainvoke_text(llm, _SYSTEM, content)


def _user_content(
    recipient: str, platform: str, company: str, role: str, context: str, resume: str
) -> str:
    return (
        f"Recipient type: {recipient.strip() or 'professional contact'}\n"
        f"Platform: {platform.strip() or 'LinkedIn'}\n"
        f"Target company: {company.strip() or '(Not specified.)'}\n"
        f"Target role: {role.strip() or '(Not specified.)'}\n\n"
        f"Context / goal of the outreach:\n{context.strip() or '(None provided.)'}\n\n"
        f"Candidate's Resume (for relevant details):\n{resume or '(Not provided.)'}\n"
    )


def stream_networking_message(
    recipient: str, platform: str, company: str, role: str, context: str, resume: str
):
    """Yield the outreach message token-by-token for SSE streaming."""
    return astream_text(
        llm, _SYSTEM, _user_content(recipient, platform, company, role, context, resume)
    )
