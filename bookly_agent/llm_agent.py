"""
Claude (Anthropic) backed agent for V3 Enterprise voice channel.

Flow per turn
-------------
1. PII/PCI guardrail check
2. Append user message to conversation history
3. Call claude-haiku-3-5 with tool definitions
4. Execute any tool calls (lookup_order, create_return, search_policy)
5. Feed tool results back to the model
6. Return final text response + trace steps

Conversation history is stored in AgentState.messages so multi-turn
context is preserved across turns within the same session.
"""
from __future__ import annotations

import json
import os
from typing import Any

import anthropic

from . import guardrails
from .orchestrator import AgentResult, AgentState
from .tools import create_return, lookup_order, search_policy


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a friendly, concise customer support agent for Bookly, \
a fictional online bookstore.

You help customers with:
- Order status inquiries
- Return and refund requests
- Questions about shipping, policies, and password reset

Rules:
- Always collect the order number (format: BLY-XXXX) before looking up an order.
- Use the provided tools to look up real data — never invent order details or policies.
- If a customer asks about something unrelated to Bookly support, politely decline \
and redirect to Bookly topics.
- Be concise. Responses are spoken aloud — use plain sentences only. \
No markdown, no bullet points, no asterisks, no headers.
- If you are missing required information, ask for it in a single, clear question.

This prompt is versioned in AGENT_DESIGN.md."""


# ---------------------------------------------------------------------------
# Tool schemas (Anthropic tool-use format)
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "lookup_order",
        "description": "Look up the status, item, and delivery details of a Bookly order.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Bookly order ID, e.g. BLY-1001",
                }
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "create_return",
        "description": "Create a return request for a delivered Bookly order.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Bookly order ID, e.g. BLY-1002",
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for the return, e.g. damaged, wrong item",
                },
            },
            "required": ["order_id", "reason"],
        },
    },
    {
        "name": "search_policy",
        "description": "Retrieve Bookly policy information on a given topic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Policy topic: shipping, returns, refunds, or password",
                }
            },
            "required": ["topic"],
        },
    },
]

# Map function name → actual callable
_TOOL_FN = {
    "lookup_order":  lambda args: lookup_order(args["order_id"]),
    "create_return": lambda args: create_return(args["order_id"], args["reason"]),
    "search_policy": lambda args: search_policy(args["topic"]),
}


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class BooklyLLMAgent:
    """Claude-backed agent used exclusively on the voice_chat_enterprise channel."""

    MODEL = "claude-haiku-4-5"

    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def handle(
        self,
        message: str,
        state: AgentState | None = None,
        channel: str = "voice_chat_enterprise",
    ) -> AgentResult:
        state = state or AgentState()
        trace: list[dict[str, Any]] = []
        text = message.strip()

        self._trace(trace, "input", "received", {"message": text, "channel": channel})

        # PII / PCI guardrail — runs before the model sees the message
        hits = guardrails.check(text)
        if hits:
            self._trace(trace, "guardrail", "pii_pci_blocked", {
                "detected": [{"category": h.category, "kind": h.kind} for h in hits],
                "action": "blocked — safe response returned, message not processed",
            })
            return AgentResult(
                response=guardrails.SAFE_RESPONSE,
                trace=trace,
                state=state,
            )

        # Append user message to conversation history
        state.messages.append({"role": "user", "content": text})

        self._trace(trace, "llm", "claude_request", {
            "model": self.MODEL,
            "history_turns": len([m for m in state.messages if m["role"] == "user"]),
        })

        # Tool-calling loop
        while True:
            response = self._client.messages.create(
                model=self.MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=state.messages,
                tools=TOOLS,
            )

            if response.stop_reason != "tool_use":
                break

            # Collect tool use blocks
            tool_uses = [b for b in response.content if b.type == "tool_use"]
            # Append full assistant response (may include text + tool_use blocks)
            state.messages.append({"role": "assistant", "content": response.content})

            # Execute each tool and collect results
            tool_results = []
            for tu in tool_uses:
                self._trace(trace, "tool", tu.name, dict(tu.input))
                result = _TOOL_FN[tu.name](tu.input)
                self._trace(trace, "tool_result", tu.name, result)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tu.id,
                    "content": json.dumps(result),
                })

            # Feed results back as a user turn
            state.messages.append({"role": "user", "content": tool_results})

        # Extract final text reply
        reply = next(
            (b.text for b in response.content if hasattr(b, "text")), ""
        )
        state.messages.append({"role": "assistant", "content": reply})

        self._trace(trace, "llm", "claude_response", {
            "model": self.MODEL,
            "stop_reason": response.stop_reason,
            "tokens": {
                "input": response.usage.input_tokens,
                "output": response.usage.output_tokens,
            },
        })

        return AgentResult(response=reply, trace=trace, state=state)

    @staticmethod
    def _trace(
        trace: list[dict[str, Any]],
        step_type: str,
        name: str,
        details: dict[str, Any],
    ) -> None:
        trace.append({"type": step_type, "name": name, "details": details})
