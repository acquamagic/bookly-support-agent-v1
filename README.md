# Bookly Support Agent

Text-first local demo for the a solutions engineering take-home. It uses simple Python orchestration, mocked support tools, and a browser UI that makes routing, memory, clarifying questions, and tool calls visible on each turn.

## Run locally

```bash
python3 app.py
```

Open http://127.0.0.1:8000.

No package install is required for this version.

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

The first phase intentionally avoids LangGraph or all-in-one agent platforms so the orchestration is easy to explain in a sales engineering demo. Voice can be added next by sending transcripts into the same `BooklySupportAgent.handle(...)` method.

