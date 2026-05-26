# Bookly Support Agent

Local support-agent demo for a my passion project to create amazing CX agents. V1 is text-first web chat; V2 adds optional browser voice chat while keeping web chat as the default. V3 (enterprise/advanced) supports pluggable, production-like voice with external providers and agile integration for future STT/TTS vendors. It uses simple Python orchestration, mocked support tools, and a browser UI that makes routing, memory, clarifying questions, and tool calls visible on each turn.

## Feature Comparison: V1 vs V2 vs V3

| Feature                              | V1: Web Chat (Baseline)                | V2: Voice Mode (Enhanced)                | V3: Enterprise/Pluggable (Agile)         |
|--------------------------------------|----------------------------------------|------------------------------------------|------------------------------------------|
| Web chat UI                          | ✅                                      | ✅                                        | ✅                                        |
| Voice chat (browser mic, STT/TTS)    | ❌                                      | ✅ (Web Speech API, SpeechSynthesis)      | ✅ (Cloud/Enterprise, pluggable)          |
| Multi-turn flows                     | ✅                                      | ✅                                        | ✅                                        |
| Clarifying questions                 | ✅                                      | ✅                                        | ✅                                        |
| Mocked order/return/policy tools     | ✅                                      | ✅                                        | ✅                                        |
| Guardrails for out-of-scope queries  | ✅                                      | ✅                                        | ✅                                        |
| Orchestration trace panel            | ✅                                      | ✅ (shows channel: web/voice)             | ✅ (shows provider/channel)               |
| Channel selection (web/voice)        | ❌                                      | ✅ (toggle in UI)                         | ✅ (toggle, provider select)              |
| Voice fallback to text input         | ❌                                      | ✅ (if mic unavailable)                   | ✅ (if provider unavailable)               |
| API keys required                    | ❌                                      | ❌ (browser default, future-ready)        | ✅ (see `.env.example`)                   |
| Future provider placeholders         | ❌                                      | ✅ (`.env.example` for STT/TTS)           | ✅ (OPENAI, Deepgram, ElevenLabs, etc.)   |
| Scalable STT/TTS (cloud)             | ❌                                      | ❌                                        | ✅ (pluggable, e.g., LiveKit)             |
| Observability integrations           | ❌                                      | ❌                                        | ✅ (logging, tracing, metrics: high-level) |
| Agile provider swap (no downtime)    | ❌                                      | ❌                                        | ✅ (modular, hot-swappable)               |

## Run locally

```bash
python3 app.py
```

Open http://127.0.0.1:8000.

No package install is required for this version.

## V1: Web Chat (Baseline)

- **Web chat only**: Users interact via a browser-based chat UI.
- **Simple agent**: Handles order status, returns, and policy questions using explicit Python orchestration.
- **Multi-turn flows**: Collects required info (order number, reason, etc.) over several turns.
- **Clarifying questions**: Asks for missing details instead of guessing.
- **Mocked tools**: No real backend; all order, return, and policy actions are simulated.
- **Guardrails**: Politely declines out-of-scope requests.
- **Trace panel**: Shows routing, memory, clarifier, and tool steps for each turn.

## V2: Voice Mode (Enhanced)

Web chat is selected by default. Click `Voice chat` to reveal the microphone button.

- **STT**: browser Web Speech API
- **TTS**: browser SpeechSynthesis
- **Required API keys**: none for the default browser mode
- **Future provider placeholders**: see `.env.example`

Voice support depends on the browser and microphone permissions. If speech recognition is unavailable, the same UI still accepts typed messages in voice mode.

## V3: Enterprise/Pluggable Voice (Agile) ✅ Complete

Click `Voice chat (Enterprise)` to activate. A mic selector dropdown appears — choose your input device, click the mic to record, click again to stop. The pipeline is:

1. Browser records audio (WebM/Opus) and POSTs it to `/api/v3/audio`
2. **Deepgram** transcribes the audio → transcript
3. `BooklySupportAgent.handle(...)` processes the transcript (same as web/V2)
4. **ElevenLabs** synthesises the agent reply → MP3 played back in the browser

Required keys in `.env`:

```
DEEPGRAM_API_KEY=...
ELEVENLABS_API_KEY=...
```

Run `pytest tests/test_voice_providers.py -v` to verify both keys are valid before demoing.

- **Mic selector**: dropdown lists all available audio input devices so you can pick the correct one (avoids silent virtual devices such as Microsoft Teams Audio)
- **File upload fallback**: use the ↑ icon to upload a pre-recorded audio file if no mic is available
- **Agile, pluggable architecture**: swap STT or TTS providers with minimal code changes
- **No vendor lock-in**: future providers integrate behind the same `deepgram_transcribe` / `elevenlabs_speak` interface
- **Debug logging intentionally left on**: the server prints `[V3] audio size`, `mime_type`, and `transcript` to the terminal on every request; the browser console logs the selected mic and recording MIME type. This is useful during demos to show the pipeline in action and diagnose any issues quickly.

## Demo paths

- Order status: `Where is my order?` then `BLY-1001`
- Return creation: `I want to return BLY-1002` then `damaged`
- Clarifying question: `I need help with my order`
- Policy lookup: `What is your shipping policy?`
- Guardrail: ask a non-Bookly question

## Architecture

- `app.py`: local web UI and JSON endpoints using Python stdlib
- `bookly_agent/orchestrator.py`: intent routing, slot filling, state, clarification, tool sequencing
- `bookly_agent/tools.py`: mocked order lookup, return creation, and policy search

The demo intentionally avoids LangGraph or all-in-one agent platforms so the orchestration is easy to explain in a sales engineering demo. V2 and V3 send voice transcripts into the same `BooklySupportAgent.handle(...)` method as web chat and mark each trace with the active channel and provider.
