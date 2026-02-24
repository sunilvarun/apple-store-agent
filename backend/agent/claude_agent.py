"""
Claude claude-sonnet-4-6 agentic loop with streaming SSE output.

Flow per turn:
  1. Add user message to session history
  2. Call Claude with tools
  3. Yield SSE events for text and tool_use blocks
  4. Execute tool calls, yield tool_result events
  5. Loop until stop_reason == "end_turn"
"""

import json
from collections import defaultdict
from typing import AsyncGenerator

import anthropic

from agent.tool_definitions import TOOLS
from agent.tool_handlers import dispatch
from config import settings

SYSTEM_PROMPT = """You are an expert iPhone advisor at the Apple Store. Your job is to help customers find the perfect iPhone based on their real needs.

RULES:
- Never invent specs, prices, or review data. Always use tools to get real data.
- If a field is missing or confidence is low, say so clearly.
- Use extract_preferences first whenever the customer describes their needs.
- Use rank_iphones (not your own intuition) to produce evidence-based rankings.
- Ask at most 2 clarifying questions before making a recommendation.
- If the customer provides an app list, factor those into usage patterns when extracting preferences.

RECOMMENDATION FORMAT:
1. Top pick: model + storage tier + price
2. Why: 2-3 specific reasons tied to their stated priorities
3. Evidence: cite spec values and review sentiment scores
4. Tradeoff: one honest limitation
5. Runner-up: one alternative if the decision is close

Keep responses concise and grounded. You are a trusted advisor, not a salesperson."""

MAX_ITERATIONS = 10


class ClaudeAgent:
    def __init__(self):
        self._sessions: dict[str, list] = defaultdict(list)

    async def stream(
        self,
        session_id: str,
        user_message: str,
        app_list: list[str] = [],
    ) -> AsyncGenerator[dict, None]:

        if not settings.ANTHROPIC_API_KEY:
            yield {"type": "error", "message": "ANTHROPIC_API_KEY not set in .env"}
            return

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        history = self._sessions[session_id]

        # Inject app list into the message if provided
        content = user_message
        if app_list:
            content += f"\n\nMy apps: {', '.join(app_list)}"

        history.append({"role": "user", "content": content})

        for iteration in range(MAX_ITERATIONS):
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=history,
            )

            # Collect assistant content blocks and yield events
            assistant_blocks = []
            for block in response.content:
                if block.type == "text":
                    yield {"type": "text", "content": block.text}
                    assistant_blocks.append({"type": "text", "text": block.text})

                elif block.type == "tool_use":
                    yield {
                        "type": "tool_use",
                        "tool": block.name,
                        "tool_use_id": block.id,
                        "input": block.input,
                    }
                    assistant_blocks.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })

            history.append({"role": "assistant", "content": assistant_blocks})

            if response.stop_reason == "end_turn":
                break

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue
                    result = dispatch(block.name, block.input)
                    yield {
                        "type": "tool_result",
                        "tool": block.name,
                        "tool_use_id": block.id,
                        "result": result,
                    }
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })
                history.append({"role": "user", "content": tool_results})
                continue

            break  # unexpected stop reason

        # Cap session history at 30 messages to avoid context bloat
        if len(history) > 30:
            self._sessions[session_id] = history[-30:]
        else:
            self._sessions[session_id] = history

        yield {"type": "done"}

    def clear_session(self, session_id: str):
        self._sessions.pop(session_id, None)


# Singleton shared across requests
agent = ClaudeAgent()
