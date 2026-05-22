from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .tools import create_return, lookup_order, search_policy


ORDER_RE = re.compile(r"\b(?:BLY[-\s]?)?\d{4}\b", re.IGNORECASE)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


@dataclass
class AgentState:
    pending_intent: str | None = None
    slots: dict[str, str] = field(default_factory=dict)


@dataclass
class AgentResult:
    response: str
    trace: list[dict[str, Any]]
    state: AgentState


class BooklySupportAgent:
    """Small, explicit Python orchestrator for the Bookly support demo."""

    def handle(
        self, message: str, state: AgentState | None = None, channel: str = "web_chat"
    ) -> AgentResult:
        state = state or AgentState()
        trace: list[dict[str, Any]] = []
        text = message.strip()
        lower = text.lower()

        self._trace(trace, "input", "received", {"message": text, "channel": channel})
        extracted = self._extract_slots(text)
        state.slots.update({key: value for key, value in extracted.items() if value})
        self._trace(trace, "memory", "updated_slots", {"slots": dict(state.slots)})

        intent = state.pending_intent or self._classify_intent(lower)
        self._trace(trace, "router", "selected_intent", {"intent": intent})

        if intent == "ambiguous_order":
            state.pending_intent = None
            return AgentResult(
                response=(
                    "I can help with that. Are you trying to check an order status, "
                    "start a return, or ask about a policy?"
                ),
                trace=trace,
                state=state,
            )

        if intent == "order_status":
            return self._handle_order_status(state, trace)

        if intent == "return_request":
            return self._handle_return(state, trace, text)

        if intent == "policy_question":
            return self._handle_policy(lower, state, trace)

        state.pending_intent = None
        self._trace(trace, "guardrail", "out_of_scope", {"decision": "decline_and_redirect"})
        return AgentResult(
            response=(
                "I’m focused on Bookly support, so I can help with order status, returns, refunds, "
                "shipping, and password reset questions. What Bookly issue should we work on?"
            ),
            trace=trace,
            state=state,
        )

    def _handle_order_status(self, state: AgentState, trace: list[dict[str, Any]]) -> AgentResult:
        state.pending_intent = "order_status"
        order_id = state.slots.get("order_id")
        if not order_id:
            self._trace(trace, "clarifier", "missing_required_slot", {"missing": "order_id"})
            return AgentResult(
                response="Sure, I can check that. What is your Bookly order number?",
                trace=trace,
                state=state,
            )

        self._trace(trace, "tool", "lookup_order", {"order_id": order_id})
        order = lookup_order(order_id)
        self._trace(trace, "tool_result", "lookup_order", order)
        if not order["found"]:
            state.slots.pop("order_id", None)
            return AgentResult(
                response=(
                    f"I couldn’t find order {order_id}. Can you double-check the order number? "
                    "Bookly order numbers look like BLY-1001."
                ),
                trace=trace,
                state=state,
            )

        state.pending_intent = None
        state.slots.clear()
        return AgentResult(
            response=(
                f"Order {order['order_id']} for *{order['item']}* is currently **{order['status']}**. "
                f"Estimated timing: {order['eta']}."
            ),
            trace=trace,
            state=state,
        )

    def _handle_return(
        self, state: AgentState, trace: list[dict[str, Any]], text: str
    ) -> AgentResult:
        state.pending_intent = "return_request"
        order_id = state.slots.get("order_id")
        if not order_id:
            self._trace(trace, "clarifier", "missing_required_slot", {"missing": "order_id"})
            return AgentResult(
                response="I can help start a return. What is the Bookly order number?",
                trace=trace,
                state=state,
            )

        reason = state.slots.get("return_reason")
        if not reason:
            inferred_reason = self._infer_return_reason(text)
            if inferred_reason:
                state.slots["return_reason"] = inferred_reason
                reason = inferred_reason

        if not reason:
            self._trace(trace, "clarifier", "missing_required_slot", {"missing": "return_reason"})
            return AgentResult(
                response="Thanks. What is the reason for the return?",
                trace=trace,
                state=state,
            )

        self._trace(trace, "tool", "lookup_order", {"order_id": order_id})
        order = lookup_order(order_id)
        self._trace(trace, "tool_result", "lookup_order", order)
        if not order["found"]:
            state.slots.pop("order_id", None)
            return AgentResult(
                response=f"I couldn’t find order {order_id}. Can you share the order number again?",
                trace=trace,
                state=state,
            )

        self._trace(trace, "tool", "create_return", {"order_id": order_id, "reason": reason})
        result = create_return(order_id, reason)
        self._trace(trace, "tool_result", "create_return", result)

        state.pending_intent = None
        state.slots.clear()
        if result["created"]:
            return AgentResult(
                response=(
                    f"Done. I created return **{result['return_id']}** for order {order_id}. "
                    "The prepaid label has been emailed to the address on the order."
                ),
                trace=trace,
                state=state,
            )
        return AgentResult(
            response=(
                f"I checked order {order_id}, but it isn’t eligible for an automated return because "
                f"its current status is **{result.get('status', 'unknown')}**. I can route this to a human "
                "support specialist if the customer still needs help."
            ),
            trace=trace,
            state=state,
        )

    def _handle_policy(
        self, lower: str, state: AgentState, trace: list[dict[str, Any]]
    ) -> AgentResult:
        state.pending_intent = None
        topic = self._policy_topic(lower)
        self._trace(trace, "tool", "search_policy", {"topic": topic})
        policy = search_policy(topic)
        self._trace(trace, "tool_result", "search_policy", policy)
        return AgentResult(response=policy["answer"], trace=trace, state=state)

    def _classify_intent(self, lower: str) -> str:
        if any(word in lower for word in ["return", "refund", "send back", "exchange"]):
            return "return_request"
        if any(word in lower for word in ["status", "track", "where is", "shipped", "order number"]):
            return "order_status"
        if "order" in lower and any(word in lower for word in ["help", "issue", "problem"]):
            return "ambiguous_order"
        if any(word in lower for word in ["shipping", "policy", "password", "reset", "delivery"]):
            return "policy_question"
        return "out_of_scope"

    def _extract_slots(self, text: str) -> dict[str, str]:
        slots: dict[str, str] = {}
        order_match = ORDER_RE.search(text)
        if order_match:
            raw = order_match.group(0).upper().replace(" ", "-")
            slots["order_id"] = raw if raw.startswith("BLY-") else f"BLY-{raw[-4:]}"
        email_match = EMAIL_RE.search(text)
        if email_match:
            slots["email"] = email_match.group(0).lower()
        return slots

    def _infer_return_reason(self, text: str) -> str | None:
        lower = text.lower().strip()
        reasons = ["damaged", "wrong item", "duplicate", "changed my mind", "late", "not needed"]
        for reason in reasons:
            if reason in lower:
                return reason
        if len(lower.split()) >= 3 and not ORDER_RE.search(text):
            return text.strip()
        return None

    def _policy_topic(self, lower: str) -> str:
        if "password" in lower or "reset" in lower:
            return "password"
        if "refund" in lower:
            return "refunds"
        if "return" in lower:
            return "returns"
        return "shipping"

    def _trace(self, trace: list[dict[str, Any]], step_type: str, name: str, details: dict[str, Any]) -> None:
        trace.append({"type": step_type, "name": name, "details": details})
