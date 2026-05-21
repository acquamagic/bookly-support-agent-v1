# PRD: Bookly Text-First Support Agent

## Summary

Build a local, text-first customer support agent for Bookly, a fictional online bookstore. The demo helps customers check order status, start returns, and answer policy questions while showing each orchestration step in a visible trace.

## Why Now

Bookly support teams need faster first responses without losing trust. The demo’s core thesis is that high-quality CX agents should be explicit about workflow: collect the right context, call the right system, avoid guessing, and escalate or clarify when confidence is low.

## Goals

- Deliver a local demo that runs on a laptop with `python3 app.py`.
- Support at least one multi-turn flow.
- Show at least one mocked tool action.
- Ask clarifying questions instead of prematurely answering ambiguous requests.
- Make orchestration visible for a solutions engineering audience.

## Non-Goals

- Production authentication, persistence, or PII controls.
- Full Bookly policy coverage.
- Voice interaction in phase one.
- LangGraph or all-in-one agent frameworks.

## Primary Users

- Bookly customer: wants quick support for common post-purchase issues.
- Bookly CX leader: wants containment without risky or fabricated answers.
- Technical evaluator: wants to see technical judgment, agent architecture, and tradeoffs.

## Phase One Scope

### Use Cases

1. Order status
   - Customer asks where an order is.
   - Agent collects order number if missing.
   - Agent calls mocked order lookup.
   - Agent returns status and estimated timing.

2. Return request
   - Customer asks to return or refund an order.
   - Agent collects order number and return reason.
   - Agent checks order eligibility.
   - Agent calls mocked return creation when eligible.

3. Policy question
   - Customer asks about shipping, returns, refunds, or password reset.
   - Agent retrieves a mocked policy answer.

4. Ambiguous request
   - Customer says something like “I need help with my order.”
   - Agent asks whether they need order status, return help, or a policy answer.

## Functional Requirements

- The user can chat in a browser UI.
- The system maintains short-lived session state for multi-turn slot filling.
- Each assistant response includes a trace with router, memory, clarifier, tool, and tool result steps where applicable.
- The demo uses mocked tools and sample orders.
- The agent declines broad out-of-scope requests and redirects to Bookly support topics.

## Product Experience

The first screen is the working support console, not a landing page. The left side contains the conversation. The right side shows the orchestration trace so the presenter can narrate what the agent is doing and why.

## Success Metrics

- Demo runs locally in under one minute.
- The return flow completes in two to three turns.
- The order-status flow demonstrates a clarifying question when the order number is missing.
- The presenter can explain every trace step without hidden framework behavior.

## Technical Decisions

1. Simple Python orchestration
   - Choice: explicit router, slot extraction, memory, and tool sequencing in Python.
   - Tradeoff: less flexible than a full agent framework.
   - Rationale: easier to demo, debug, and defend in a four-hour SE assignment.

2. Mocked tools
   - Choice: local order, return, and policy tools.
   - Tradeoff: no real backend integration.
   - Rationale: keeps attention on workflow design and decision quality.

3. Deterministic first phase
   - Choice: rule-based intent routing for the first version.
   - Tradeoff: less natural language coverage than an LLM router.
   - Rationale: reliable local demo; an LLM router can be added later behind the same interface.

## Phase Two: Voice Agent

Voice should reuse the same orchestration interface. Speech-to-text produces a transcript, `BooklySupportAgent.handle(...)` processes it, and text-to-speech returns the response. The orchestration trace remains visible for the presenter and support supervisor.

## Open Questions

- Which LLM provider should be used for the next iteration, if any?
- Should the final demo emphasize CX leadership value, technical architecture, or both equally?
- Should the pitch deck include Snyk-style trust, governance, and risk framing as part of the story?

