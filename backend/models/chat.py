from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str    # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    session_id: str
    app_list: list[str] = []
    budget_max: int | None = None
