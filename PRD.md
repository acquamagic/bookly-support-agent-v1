# PRD: Bookly Support Agent V2/V3

## Summary

Build a local customer support agent for Bookly, a fictional online bookstore. V1 provides web chat. V2 adds optional voice chat while keeping web chat as the default. The demo helps customers check order status, start returns, and answer policy questions while showing each orchestration step in a visible trace.

## Why Now

Bookly support teams need faster first responses without losing trust. The demo’s core thesis is that high-quality CX agents should be explicit about workflow: collect the right context, call the right system, avoid guessing, and escalate or clarify when confidence is low.

## Goals

- Deliver a local demo that runs on a laptop with `python3 app.py`.
- Support at least one multi-turn flow.
- Show at least one mocked tool action.
- Ask clarifying questions instead of prematurely answering ambiguous requests.
- Make orchestration visible for a solutions engineering audience.
- Add a voice-chat path without replacing the default web-chat path.

## Non-Goals

- Production authentication, persistence, or PII controls.
- Full Bookly policy coverage.
- LangGraph or all-in-one agent frameworks.
- Production telephony, call recording, or streaming voice infrastructure.

## Primary Users

- Bookly customer: wants quick support for common post-purchase issues.
- Bookly CX leader: wants containment without risky or fabricated answers.
- Technical evaluator: wants to see technical judgment, agent architecture, and tradeoffs.

## V1 Web-Chat Scope

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
- The user can choose web chat or voice chat, with web chat selected by default.
- The system maintains short-lived session state for multi-turn slot filling.
- Each assistant response includes a trace with router, memory, clarifier, tool, and tool result steps where applicable.
- The demo uses mocked tools and sample orders.
- The agent declines broad out-of-scope requests and redirects to Bookly support topics.

## Product Experience

The first screen is the working support console, not a landing page. The left side contains the conversation, examples, web-chat and voice-chat controls, and composer. The right side shows the orchestration trace so the presenter can narrate what the agent is doing and why.

## V2 Voice-Chat Scope

1. Mode selection
   - Web chat is active by default.
   - Voice chat is enabled when the user clicks the voice-chat control.
   - The same conversation and trace panels are used for both modes.

2. Speech-to-text
   - Default provider: browser Web Speech API.
   - No API key is required for the default browser provider.
   - The recognized transcript is sent to `/chat` with `channel: "voice_chat"`.

3. Text-to-speech
   - Default provider: browser SpeechSynthesis.
   - No API key is required for the default browser provider.
   - Assistant replies are read aloud only while voice chat is active.

4. Provider readiness
   - `.env.example` includes placeholders for future OpenAI, Deepgram, and ElevenLabs keys.
   - The current implementation does not transmit audio or text to external STT/TTS providers.

## Success Metrics

- Demo runs locally in under one minute.
- The return flow completes in two to three turns.
- The order-status flow demonstrates a clarifying question when the order number is missing.
- The presenter can explain every trace step without hidden framework behavior.
- Voice chat can complete at least one policy or order-status turn in browsers that support speech recognition.

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

Voice reuses the same orchestration interface. Speech-to-text produces a transcript, `BooklySupportAgent.handle(...)` processes it, and text-to-speech returns the response. The orchestration trace remains visible for the presenter and support supervisor.

## V3: Pluggable, Enterprise-Ready Voice (Agile Integration) ✅ Complete

- **Voice chat (Enterprise)** mode is fully implemented and tested end-to-end.
- **STT**: Deepgram (`nova-2` model, `smart_format=true`). Audio recorded as `audio/webm;codecs=opus` in the browser and POSTed to `/api/v3/audio`.
- **TTS**: ElevenLabs (voice `EXAVITQu4vr4xnSDxMaL`). Agent reply is synthesised to MP3 and played back in the browser automatically.
- **Mic selector UI**: dropdown lists all audio input devices so presenters can pick the correct hardware mic (avoids silent virtual devices).
- **File upload fallback**: upload icon lets users send a pre-recorded audio file when no mic is available.
- **Key validation**: `pytest tests/test_voice_providers.py -v` verifies both API keys authenticate and return valid responses before a demo.
- **Debug logging intentionally left on**: server prints `[V3] audio size`, `mime_type`, and `transcript` on every request; browser console logs the selected mic and recording MIME type. This is useful for live demos and rapid diagnosis.
- Architecture is designed for **agile, pluggable provider integration**: swap STT or TTS components (e.g., add LiveKit) with minimal/no downtime.
- No vendor lock-in: future providers integrate behind the same `deepgram_transcribe` / `elevenlabs_speak` interface.

## Open Questions

- Which LLM provider should be used for the next iteration, if any?
- Should the final demo emphasize CX leadership value, technical architecture, or both equally?
- Should the pitch deck include Snyk-style trust, governance, and risk framing as part of the story?
