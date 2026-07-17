import json
from typing import AsyncIterator

from fastapi.responses import StreamingResponse


async def _sse_frames(chunks: AsyncIterator[str]) -> AsyncIterator[str]:
    """Wrap a stream of text chunks as Server-Sent Events.

    Each chunk is JSON-encoded so embedded newlines never break SSE framing.
    A final `done` event signals completion; errors are reported inline so the
    client can surface them instead of hanging.
    """
    try:
        async for chunk in chunks:
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
    except Exception as exc:  # noqa: BLE001 - report any generation error to the client
        yield f"data: {json.dumps({'error': str(exc)})}\n\n"
    finally:
        yield f"data: {json.dumps({'done': True})}\n\n"


def sse_response(chunks: AsyncIterator[str]) -> StreamingResponse:
    """Return a StreamingResponse that emits the chunks as an SSE text stream."""
    return StreamingResponse(
        _sse_frames(chunks),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
