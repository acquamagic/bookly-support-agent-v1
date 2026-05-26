# Bookly Support Agent — Design Document

## Architecture Overview

```
Browser UI
  │
  ├── /chat          (V1 Web Chat, V2 Browser Voice)
  │     └── BooklySupportAgent  ← rule-based Python orchestrator
  │
  └── /api/v3/audio  (V3 Enterprise Voice)
        ├── Deepgram  ← speech-to-text (audio/webm → transcript)
        ├── PII/PCI Guardrail  ← blocks before LLM sees the message
        ├── Claude claude-haiku-4-5  ← intent + tool calling
        │     ├── lookup_order(order_id)   → mocked order management system
        │     ├── create_return(order_id, reason) → mocked returns system
        │     └── search_policy(topic)     → mocked knowledge base
        └── ElevenLabs  ← text-to-speech (response → MP3)
```

**Components:**
- `app.py` — stdlib HTTP server, session management, V3 pipeline orchestration
- `bookly_agent/orchestrator.py` — rule-based intent router, slot filler, clarifier (V1/V2)
- `bookly_agent/llm_agent.py` — Claude-backed agent with tool use (V3)
- `bookly_agent/tools.py` — mocked order, return, and policy tools
- `bookly_agent/guardrails.py` — PII/PCI pattern detection, runs before LLM
- `bookly_agent/voice_providers.py` — Deepgram STT, ElevenLabs TTS
- Session state (`AgentState`) held in memory per session ID; includes conversation
  history for multi-turn LLM context

**Observability:** every V3 request logs STT, LLM, TTS, and end-to-end latency to
the terminal and renders them in the browser trace panel.

---

## Conversation & Decision Design

**V1/V2 (rule-based):** keyword intent classification → regex slot extraction →
clarifying question if slot missing → mocked tool call → templated response.
Deterministic and easy to explain in a demo.

**V3 (LLM-backed):** Claude receives the full conversation history and a set of
tool definitions. It decides when to ask a clarifying question, when to call a
tool, and how to phrase the response. Key design choices:

| Decision | Design | Rationale |
|---|---|---|
| Ask before acting | Claude asks for order number before calling `lookup_order` | Prevents wasted tool calls and mirrors good support practice |
| Tool-first, not prompt-first | Order data and policies come from tools, not the system prompt | Eliminates hallucination on factual data |
| Short conversation history | Full history passed each turn | Enables natural multi-turn slot collection without explicit state machines |
| Voice-optimised output | System prompt explicitly bans markdown, bullets, and headers | Responses are read aloud by ElevenLabs — formatting breaks TTS |
| Out-of-scope redirect | System prompt instructs Claude to decline non-Bookly topics | Keeps the agent focused; avoids liability from off-topic advice |

---

## Hallucination & Safety Controls

**Grounding via tools:** Claude is instructed to never invent order details or
policies. All factual answers come from tool return values. If `lookup_order`
returns `found: false`, Claude tells the customer the order wasn't found — it
cannot fabricate a status.

**PII/PCI guardrail (`bookly_agent/guardrails.py`):** runs before every message
reaches Claude. Detects and blocks:
- Payment card numbers (Luhn-validated, 13–19 digits)
- CVV/CVC codes
- Card expiry dates
- US Social Security Numbers
- US phone numbers
- Passwords

On detection the message is dropped, a safe refusal is returned, and a
`guardrail/pii_pci_blocked` step appears in the trace. The raw message never
reaches the LLM, tools, or logs.

**Out-of-scope guardrail:** the rule-based router (V1/V2) returns a fixed
redirect for unrecognised intents. Claude (V3) is prompted to do the same.

---

## System Prompt (V3)

```
You are a friendly, concise customer support agent for Bookly,
a fictional online bookstore.

You help customers with:
- Order status inquiries
- Return and refund requests
- Questions about shipping, policies, and password reset

Rules:
- Always collect the order number (format: BLY-XXXX) before looking up an order.
- Use the provided tools to look up real data — never invent order details or policies.
- If a customer asks about something unrelated to Bookly support, politely decline
  and redirect to Bookly topics.
- Be concise. Responses are spoken aloud — use plain sentences only. No markdown,
  no bullet points, no asterisks, no headers.
- If you are missing required information, ask for it in a single, clear question.
```

---

## Production Readiness

**Tradeoffs made to move quickly:**

| Shortcut | Production alternative |
|---|---|
| In-memory session store (`dict`) | Redis / DynamoDB with TTL |
| Mocked tools (hardcoded orders) | Real OMS, returns, and KB API calls |
| No authentication | JWT / OAuth2 per session |
| Single-threaded tool calls | Parallel tool execution for multi-tool turns |
| `claude-haiku-4-5` for speed | `claude-sonnet-4-5` or `claude-opus-4-5` for complex edge cases |
| Regex-based PII detection | ML-based NER (e.g. AWS Comprehend, Presidio) for higher recall |
| No prompt versioning | Prompt registry with A/B testing and rollback |
| STT/TTS as synchronous blocking calls | Streaming STT + streaming TTS for sub-second first-word latency |
| No rate limiting | Per-session and per-IP rate limits on `/api/v3/audio` |
| No persistent conversation logs | Append-only log store for QA, fine-tuning, and compliance |

**What I would prioritise first for production:**
1. Real tool integrations — the orchestration logic is already correct, just swap mocks
2. Streaming TTS — biggest latency win; ElevenLabs supports chunked streaming
3. Conversation logging — needed for QA, trust, and model improvement
4. Auth — required before any real customer data flows through the agent
