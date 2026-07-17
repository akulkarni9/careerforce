import json
import re
from typing import Any, AsyncIterator, Awaitable, cast

from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from config import settings


# Shared guardrails prepended to every node's system prompt so tone, length,
# grounding and the internal-reasoning contract are consistent across the app.
STYLE_GUARDRAILS = """You operate inside an automated pipeline. Follow these global rules in addition to your task-specific instructions below.

Reasoning:
- Think silently and briefly before answering; do NOT write your reasoning, notes, or a scratchpad in the output. Your entire token budget must go to the final answer.
- Output only the final user-facing answer and nothing else.

Output quality:
- The final answer must follow the exact Markdown structure specified in your task, with no preamble, sign-off, or meta commentary.
- Be concise, specific, and skimmable. No filler, hedging, or repetition. Prefer concrete nouns, tools, and numbers over vague adjectives.
- Ground every claim in the information provided. Never fabricate facts, experience, employers, metrics, or requirements. If something is unknown, say so plainly.
- Use plain Markdown only (headings, bullets, bold). Do not wrap the whole response in a code block.

--- TASK INSTRUCTIONS ---
"""

# Streaming variant: no <scratchpad> so tokens can be sent to the user directly
# without leaking or having to buffer/strip private reasoning mid-stream.
STREAM_GUARDRAILS = """You operate inside an automated pipeline. Follow these global rules in addition to your task-specific instructions below.

Output quality:
- Think silently; output only the final user-facing answer, with no preamble, sign-off, or meta commentary.
- Follow the exact Markdown structure specified in your task.
- Be concise, specific, and skimmable. No filler, hedging, or repetition. Prefer concrete nouns, tools, and numbers over vague adjectives.
- Ground every claim in the information provided. Never fabricate facts, experience, employers, metrics, or requirements. If something is unknown, say so plainly.
- Use plain Markdown only (headings, bullets, bold). Do not wrap the whole response in a code block.

--- TASK INSTRUCTIONS ---
"""

_SCRATCHPAD_RE = re.compile(r"<scratchpad>.*?</scratchpad>", re.DOTALL | re.IGNORECASE)


def build_llm(
    temperature: float,
    num_predict: int | None = None,
    json_mode: bool = False,
) -> ChatOllama:
    """Create a ChatOllama client with the project-wide context and output limits.

    Ollama defaults num_ctx to ~4096, which silently truncates long prompts
    (resume + JD + RAG context). Gemma supports a far larger window, so we set
    it explicitly here for every node.

    num_predict caps how many tokens the model may generate. Pass a larger value
    for long-form outputs (cover letters, multi-week plans, negotiation scripts)
    so they are not cut off; omit it to use the project default.

    json_mode constrains the model to emit valid JSON via Ollama's structured
    decoding. This must be set at construction (Ollama reads `format` at build
    time, not from per-call kwargs), so it lives here rather than in a bind.
    """
    return ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=temperature,
        num_ctx=settings.OLLAMA_NUM_CTX,
        num_predict=num_predict if num_predict is not None else settings.OLLAMA_NUM_PREDICT,
        keep_alive=settings.OLLAMA_KEEP_ALIVE,
        format="json" if json_mode else None,
    )


def content_to_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        items = cast(list[object], content)
        parts: list[str] = []
        for item in items:
            if isinstance(item, str):
                parts.append(item)
            else:
                parts.append(json.dumps(item, ensure_ascii=True, default=str))
        return "\n".join(parts)
    return str(content)


def _strip_scratchpad(text: str) -> str:
    """Remove the model's private <scratchpad> reasoning from the user-facing text.

    Handles the normal closed block, and the defensive case where the model
    emitted an opening tag but the closing tag was cut off by num_predict.
    """
    cleaned = _SCRATCHPAD_RE.sub("", text)
    lower = cleaned.lower()
    if "<scratchpad>" in lower and "</scratchpad>" not in lower:
        # Unterminated scratchpad: drop everything from the opening tag onward.
        cleaned = cleaned[: lower.index("<scratchpad>")]
    return cleaned.strip()


async def ainvoke_text(llm: ChatOllama, system: str, user_content: object) -> str:
    """Invoke the model with a system instruction and user content, returning text.

    The shared STYLE_GUARDRAILS are prepended to the task system prompt, and any
    private <scratchpad> reasoning is stripped from the result.
    user_content may be a plain string or a multimodal content list (text + image).
    """
    response: BaseMessage = await cast(
        Awaitable[BaseMessage],
        llm.ainvoke(
            [
                SystemMessage(content=STYLE_GUARDRAILS + system),
                HumanMessage(content=cast(Any, user_content)),
            ]
        ),
    )
    response_any: Any = cast(Any, response)
    text = _strip_scratchpad(content_to_text(cast(object, response_any.content)))
    if not text:
        # The model returned nothing usable (e.g. it emitted only private
        # reasoning that got stripped, or hit the token cap before answering).
        # Fail loudly so the endpoint returns an error instead of silently
        # passing an empty string downstream (which the next node would then
        # "fill in" with hallucinated placeholders like "[No data provided]").
        raise RuntimeError("The model returned an empty response. Please try again.")
    return text


async def ainvoke_messages(
    llm: ChatOllama, system: str, messages: list[BaseMessage]
) -> str:
    """Invoke the model with a full conversation history, returning text.

    Used by multi-turn features (e.g. the mock interviewer). The shared
    STYLE_GUARDRAILS are prepended to the task system prompt, the prior turns
    are replayed, and any private <scratchpad> reasoning is stripped.
    """
    response: BaseMessage = await cast(
        Awaitable[BaseMessage],
        llm.ainvoke([SystemMessage(content=STYLE_GUARDRAILS + system), *messages]),
    )
    response_any: Any = cast(Any, response)
    return _strip_scratchpad(content_to_text(cast(object, response_any.content)))


async def ainvoke_json(llm: ChatOllama, system: str, user_content: str) -> dict[str, Any]:
    """Invoke a JSON-mode model and return the parsed object.

    The `llm` must be built with `json_mode=True` so Ollama constrains it to
    valid JSON. This is far more robust than regex-parsing prose for
    machine-readable fields (scores, tags, booleans). The system prompt must
    describe the exact JSON schema expected.
    """
    response: BaseMessage = await cast(
        Awaitable[BaseMessage],
        llm.ainvoke(
            [
                SystemMessage(content=system),
                HumanMessage(content=user_content),
            ]
        ),
    )
    response_any: Any = cast(Any, response)
    raw = content_to_text(cast(object, response_any.content)).strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # Defensive: pull the first {...} block if the model added stray text.
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return {}
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}
    return parsed if isinstance(parsed, dict) else {}


async def ainvoke_refine(
    llm: ChatOllama,
    system: str,
    user_content: str,
    critic_focus: str,
) -> str:
    """Two-pass draft -> self-critique -> improved final answer.

    A capable model produces noticeably better output when it critiques its own
    first attempt and rewrites, rather than one-shotting. The scratchpad is
    stripped from both passes. `critic_focus` describes what the revision must
    optimise for (e.g. specificity, keyword alignment, tone).
    """
    draft = await ainvoke_text(llm, system, user_content)
    refine_system, refine_input = _refine_prompts(system, user_content, critic_focus, draft)
    return await ainvoke_text(llm, refine_system, refine_input)


def _refine_prompts(
    system: str, user_content: str, critic_focus: str, draft: str
) -> tuple[str, str]:
    """Build the revision-pass system prompt and input from a first draft."""
    refine_system = (
        system
        + "\n\n--- REVISION PASS ---\n"
        + "You previously produced the DRAFT below. Critique it privately against these priorities, "
        + f"then output an improved final version:\n{critic_focus}\n"
        + "Keep everything that is strong. Fix weak, vague, generic, or unsupported parts. "
        + "Output ONLY the final improved answer in the exact required Markdown structure — no critique, no preamble."
    )
    refine_input = f"{user_content}\n\n--- DRAFT TO IMPROVE ---\n{draft}"
    return refine_system, refine_input


async def astream_refine(
    llm: ChatOllama,
    system: str,
    user_content: str,
    critic_focus: str,
) -> AsyncIterator[str]:
    """Two-pass refine that streams the final improved answer token-by-token.

    The draft pass is buffered (the client shows a brief "polishing" state),
    then the revision pass streams so these long, high-value outputs still give
    live feedback instead of a silent wait. Keeps the quality of the two-pass
    approach while matching the streaming UX of the other tools.
    """
    draft = await ainvoke_text(llm, system, user_content)
    refine_system, refine_input = _refine_prompts(system, user_content, critic_focus, draft)
    async for chunk in astream_text(llm, refine_system, refine_input):
        yield chunk


async def astream_text(
    llm: ChatOllama, system: str, user_content: object
) -> AsyncIterator[str]:
    """Stream the model's answer token-by-token as plain text chunks.

    Uses STREAM_GUARDRAILS (no <scratchpad>) so chunks can be forwarded to the
    client directly without leaking or having to buffer private reasoning.
    """
    async for chunk in llm.astream(
        [
            SystemMessage(content=STREAM_GUARDRAILS + system),
            HumanMessage(content=cast(Any, user_content)),
        ]
    ):
        chunk_any: Any = cast(Any, chunk)
        text = content_to_text(cast(object, chunk_any.content))
        if text:
            yield text


