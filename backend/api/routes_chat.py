import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from agent.claude_agent import agent
from models.chat import ChatRequest

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def chat(request: ChatRequest):
    user_message = request.messages[-1].content if request.messages else ""

    async def event_stream():
        async for event in agent.stream(
            session_id=request.session_id,
            user_message=user_message,
            app_list=request.app_list,
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.delete("/{session_id}")
def clear_session(session_id: str):
    agent.clear_session(session_id)
    return {"status": "cleared"}
