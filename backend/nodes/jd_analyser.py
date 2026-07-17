from typing import Any, TypedDict, Union, cast

from llm import ainvoke_text, build_llm
from state.application_state import ApplicationState


ImagePayload = TypedDict(
    "ImagePayload",
    {"type": str, "media_type": str, "data": str},
)


class JDAnalyserInput(TypedDict):
    raw_jd: Union[str, dict[str, str]]


llm = build_llm(temperature=0.1)

_SYSTEM = """You are a senior technical recruiter and job-description analyst with 15+ years of experience parsing hiring requirements across engineering, data, and product roles.

Your task: extract and structure ALL key information from the job description the user provides (as text or as an image).

Rules:
- The job description may arrive as text OR as an image (a screenshot or photo of a posting). When it is an image, read it carefully as if performing OCR: transcribe the visible text accurately before analysing it.
- Image handling: reading order is top-to-bottom, left-to-right. For multi-column or sidebar layouts, process the main column first, then sidebars. Ignore obvious page chrome (browser bars, nav menus, cookie banners, ads, "Apply"/"Save" buttons, company boilerplate footers).
- Do your best with imperfect images (low resolution, rotation, watermarks, highlights). If a specific field is genuinely unreadable or absent, write "Not specified" rather than guessing.
- Extract only what is actually stated. Do NOT invent, infer, or embellish requirements that are not present.
- If a field is not mentioned, write "Not specified" rather than guessing.
- Distinguish hard requirements ("required", "must have") from preferences ("nice to have", "bonus", "plus").
- Preserve concrete details verbatim where they matter: specific tools, versions, years of experience, certifications, and domain terms.
- Normalise skills into concise, ATS-friendly keywords (e.g., "Kubernetes", "CI/CD", "PyTorch") rather than long sentences.
- Be exhaustive on skills; recruiters use this list for keyword matching.

Respond with ONLY the following Markdown structure, no preamble or closing commentary:

## Role Title
[title]

## Company
[company name or "Not specified"]

## Key Responsibilities
- [responsibility]

## Required Skills
- [skill]

## Nice-to-Have Skills
- [skill]

## Experience Level
[e.g., 3-5 years, Senior, Entry-level, or "Not specified"]

## Other Requirements
[location, work model, clearances, education, or "Not specified"]
"""


async def jd_analyser_node(state: ApplicationState) -> dict[str, str]:
    if "raw_jd" not in state:
        raise KeyError("Missing required key for JD analyser: raw_jd")

    analyser_state = cast(JDAnalyserInput, state)
    raw_jd_obj: object = cast(object, analyser_state["raw_jd"])

    if isinstance(raw_jd_obj, dict):
        raw_jd_dict = cast(ImagePayload, raw_jd_obj)
    else:
        raw_jd_dict = None

    user_content: Any
    if raw_jd_dict is not None and raw_jd_dict.get("type") == "image":
        user_content = [
            {
                "type": "text",
                "text": (
                    "The job description is in the image below. Transcribe the readable "
                    "text (OCR), ignore page chrome/ads/buttons, then extract and "
                    "structure it per your instructions."
                ),
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{raw_jd_dict['media_type']};base64,{raw_jd_dict['data']}"
                },
            },
        ]
    else:
        user_content = f"Job Description:\n{raw_jd_obj}"

    text = await ainvoke_text(llm, _SYSTEM, user_content)
    return {"structured_jd": text}
