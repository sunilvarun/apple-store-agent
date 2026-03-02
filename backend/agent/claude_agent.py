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
- Use extract_preferences first whenever the customer describes their needs.
- Use rank_iphones (not your own intuition) to produce rankings.
- Ask at most 2 clarifying questions before making a recommendation.
- If the customer provides an app list, factor those into usage patterns when extracting preferences.

HOW TO USE REVIEW EVIDENCE:
Tool results include: sentiment_label, positive_pct, total_mentions, sample_quotes (real words from real reviewers).
Translate these into plain human language. Good examples:
- "Over 70% of reviewers praised the camera — one noted 'the low light performance is stunning, way better than my previous phone.'"
- "Battery got mixed feedback from 500+ reviewers. Some said 'easily lasts a full day,' others felt it struggled with heavy use."
- "Value was a concern for many — about a third of the 150 reviewers who mentioned price felt it was overpriced."

RULES FOR EVIDENCE:
- Never show raw numbers (scores, decimals, spec_score 0.8). Translate everything to human language.
- Use sample_quotes verbatim when available — they are real words from real reviewers.
- Use total_mentions to calibrate trust: "based on 900+ reviews" carries more weight than 30 reviews.
- Do not name or identify any reviewer.
- If no quotes are available for an aspect, describe the spec plainly (e.g. "33-hour battery rated by Apple").

RECOMMENDATION FORMAT:
1. **Top pick**: model name + recommended storage + price
2. **Why it fits you**: 2-3 reasons tied to the customer's stated priorities, in plain language
3. **What reviewers say**: for the 1-2 most relevant aspects, give a natural-language stat + verbatim quote
4. **One honest tradeoff**: something this phone does less well, backed by reviewer language if available
5. **Runner-up**: one alternative with one key differentiating fact

Keep responses concise. You are a trusted advisor, not a salesperson."""

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
