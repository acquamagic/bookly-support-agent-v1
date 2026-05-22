# Bookly Support Agent

Local support-agent demo for a solutions engineering take-home. V1 is text-first; V2 adds optional browser voice chat while keeping web chat as the default. It uses simple Python orchestration, mocked support tools, and a browser UI that makes routing, memory, clarifying questions, and tool calls visible on each turn.

## Run locally

```bash
python3 app.py
```

Open http://127.0.0.1:8000.

No package install is required for this version.

## V2 voice mode

Web chat is selected by default. Click `Voice chat` to reveal the microphone button.

- STT: browser Web Speech API
- TTS: browser SpeechSynthesis
- Required API keys: none for the default browser mode
- Future provider placeholders: see `.env.example`

Voice support depends on the browser and microphone permissions. If speech recognition is unavailable, the same UI still accepts typed messages in voice mode.

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

The demo intentionally avoids LangGraph or all-in-one agent platforms so the orchestration is easy to explain in a sales engineering demo. V2 sends voice transcripts into the same `BooklySupportAgent.handle(...)` method as web chat and marks each trace with the active channel.
