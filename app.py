from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from uuid import uuid4

from bookly_agent.orchestrator import AgentState, BooklySupportAgent


HOST = "127.0.0.1"
PORT = 8000

agent = BooklySupportAgent()
sessions: dict[str, AgentState] = {}


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Bookly Support Agent</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #17202a;
      --muted: #5f6b7a;
      --line: #d8dee7;
      --panel: #f7f9fb;
      --accent: #0f766e;
      --accent-strong: #115e59;
      --voice: #7c2d12;
      --voice-bg: #fff7ed;
      --user: #e7f5f2;
      --agent: #ffffff;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: #eef3f7;
    }
    .app {
      min-height: 100vh;
      display: grid;
      grid-template-columns: minmax(0, 1fr) 380px;
    }
    main {
      display: flex;
      flex-direction: column;
      min-width: 0;
      border-right: 1px solid var(--line);
      background: #ffffff;
    }
    header {
      padding: 18px 24px;
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    h1 {
      margin: 0;
      font-size: 20px;
      line-height: 1.2;
      letter-spacing: 0;
    }
    .subtitle {
      margin-top: 4px;
      color: var(--muted);
      font-size: 13px;
    }
    button {
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      border-radius: 6px;
      padding: 9px 12px;
      font: inherit;
      cursor: pointer;
    }
    button.primary {
      border-color: var(--accent);
      background: var(--accent);
      color: #fff;
      font-weight: 650;
    }
    button.primary:hover { background: var(--accent-strong); }
    button.icon {
      width: 44px;
      min-width: 44px;
      padding: 0;
      display: inline-grid;
      place-items: center;
    }
    button.icon svg {
      width: 18px;
      height: 18px;
      stroke-width: 2.2;
    }
    button.icon.active {
      border-color: var(--voice);
      background: var(--voice-bg);
      color: var(--voice);
    }
    .mode-bar {
      padding: 12px 24px 0;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      border-top: 1px solid var(--line);
    }
    .mode-buttons {
      display: flex;
      gap: 8px;
    }
    .mode-button {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      min-height: 36px;
      color: var(--muted);
    }
    .mode-button svg {
      width: 17px;
      height: 17px;
      stroke-width: 2.2;
    }
    .mode-button.active {
      border-color: var(--accent);
      color: var(--accent-strong);
      background: var(--user);
      font-weight: 650;
    }
    .mode-button.voice.active {
      border-color: var(--voice);
      color: var(--voice);
      background: var(--voice-bg);
    }
    .voice-status {
      min-height: 18px;
      color: var(--muted);
      font-size: 13px;
      overflow-wrap: anywhere;
      text-align: right;
    }
    #chat {
      flex: 1;
      overflow: auto;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }
    .message {
      max-width: 760px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px 14px;
      line-height: 1.45;
      white-space: pre-wrap;
    }
    .message.user {
      align-self: flex-end;
      background: var(--user);
      border-color: #b7ddd5;
    }
    .message.agent {
      align-self: flex-start;
      background: var(--agent);
    }
    form {
      display: flex;
      gap: 10px;
      padding: 16px 24px 22px;
      border-top: 1px solid var(--line);
      background: #fff;
    }
    input {
      flex: 1;
      min-width: 0;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 12px 13px;
      font: inherit;
    }
    aside {
      background: var(--panel);
      display: flex;
      flex-direction: column;
      min-width: 0;
    }
    .trace-header {
      padding: 18px 18px 12px;
      border-bottom: 1px solid var(--line);
    }
    .trace-header h2 {
      margin: 0;
      font-size: 16px;
      letter-spacing: 0;
    }
    .trace-header p {
      margin: 5px 0 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.35;
    }
    #trace {
      overflow: auto;
      padding: 14px 14px 20px;
      display: grid;
      gap: 10px;
    }
    .step {
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
    }
    .step-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 7px;
    }
    .pill {
      font-size: 11px;
      text-transform: uppercase;
      color: #fff;
      background: #3b5b6f;
      border-radius: 999px;
      padding: 3px 7px;
      white-space: nowrap;
    }
    .step-name {
      font-weight: 700;
      font-size: 13px;
      overflow-wrap: anywhere;
    }
    pre {
      margin: 0;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }
    .examples {
      padding: 0 24px 12px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .examples button {
      font-size: 13px;
      padding: 7px 9px;
      color: var(--muted);
    }
    @media (max-width: 560px) {
      header, #chat, .examples, .mode-bar, form {
        padding-left: 16px;
        padding-right: 16px;
      }
      .mode-bar {
        align-items: flex-start;
        flex-direction: column;
      }
      .voice-status {
        text-align: left;
      }
    }
    @media (max-width: 860px) {
      .app { grid-template-columns: 1fr; }
      aside {
        min-height: 280px;
        border-top: 1px solid var(--line);
      }
      main { border-right: 0; min-height: 65vh; }
    }
  </style>
</head>
<body>
  <div class="app">
    <main>
      <header>
        <div>
          <h1>Bookly Support Agent</h1>
          <div class="subtitle">V2 demo with web chat by default and optional browser voice chat</div>
        </div>
        <button id="reset" type="button">Reset</button>
      </header>
      <div id="chat"></div>
      <div class="examples">
        <button data-example="Where is my order?">Order status</button>
        <button data-example="I want to return BLY-1002">Return flow</button>
        <button data-example="What is your shipping policy?">Policy question</button>
      </div>
      <div class="mode-bar" aria-label="Conversation mode">
        <div class="mode-buttons">
          <button id="web-chat-mode" class="mode-button active" type="button" aria-pressed="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
              <path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z"></path>
            </svg>
            Web chat
          </button>
          <button id="voice-chat-mode" class="mode-button voice" type="button" aria-pressed="false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
              <path d="M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3Z"></path>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
              <path d="M12 19v3"></path>
            </svg>
            Voice chat
          </button>
        </div>
        <div id="voice-status" class="voice-status">Web chat is selected.</div>
      </div>
      <form id="form">
        <button id="voice" class="icon" type="button" aria-label="Start voice input" title="Start voice input" hidden>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
            <path d="M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3Z"></path>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
            <path d="M12 19v3"></path>
          </svg>
        </button>
        <input id="message" autocomplete="off" placeholder="Ask about an order, return, refund, shipping, or password reset">
        <button class="primary" type="submit">Send</button>
      </form>
    </main>
    <aside>
      <div class="trace-header">
        <h2>Tool Orchestration</h2>
        <p>Each turn shows routing, memory, clarifying questions, and mocked tool calls.</p>
      </div>
      <div id="trace"></div>
    </aside>
  </div>
  <script>
    let sessionId = localStorage.getItem("bookly_session_id") || crypto.randomUUID();
    localStorage.setItem("bookly_session_id", sessionId);

    const chat = document.querySelector("#chat");
    const trace = document.querySelector("#trace");
    const form = document.querySelector("#form");
    const input = document.querySelector("#message");
    const webChatMode = document.querySelector("#web-chat-mode");
    const voiceChatMode = document.querySelector("#voice-chat-mode");
    const voiceButton = document.querySelector("#voice");
    const voiceStatus = document.querySelector("#voice-status");
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = SpeechRecognition ? new SpeechRecognition() : null;
    let activeChannel = "web_chat";
    let isListening = false;

    if (recognition) {
      recognition.lang = "en-US";
      recognition.interimResults = false;
      recognition.continuous = false;

      recognition.addEventListener("start", () => {
        isListening = true;
        voiceButton.classList.add("active");
        voiceButton.setAttribute("aria-label", "Stop voice input");
        voiceButton.title = "Stop voice input";
        voiceStatus.textContent = "Listening...";
      });

      recognition.addEventListener("result", event => {
        const transcript = event.results[0][0].transcript.trim();
        voiceStatus.textContent = `Heard: ${transcript}`;
        if (transcript) sendMessage(transcript, "voice_chat");
      });

      recognition.addEventListener("error", event => {
        voiceStatus.textContent = `Voice input stopped: ${event.error.replace(/-/g, " ")}`;
      });

      recognition.addEventListener("end", () => {
        isListening = false;
        voiceButton.classList.remove("active");
        voiceButton.setAttribute("aria-label", "Start voice input");
        voiceButton.title = "Start voice input";
      });
    }

    function addMessage(role, text) {
      const node = document.createElement("div");
      node.className = `message ${role}`;
      node.innerHTML = text.replace(/\\*\\*(.*?)\\*\\*/g, "<strong>$1</strong>").replace(/\\*(.*?)\\*/g, "<em>$1</em>");
      chat.appendChild(node);
      chat.scrollTop = chat.scrollHeight;
    }

    function renderTrace(steps) {
      trace.innerHTML = "";
      for (const step of steps) {
        const node = document.createElement("div");
        node.className = "step";
        node.innerHTML = `
          <div class="step-top">
            <span class="pill">${step.type}</span>
            <span class="step-name">${step.name}</span>
          </div>
          <pre>${escapeHtml(JSON.stringify(step.details, null, 2))}</pre>
        `;
        trace.appendChild(node);
      }
    }

    function escapeHtml(text) {
      return text.replace(/[&<>"']/g, char => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
      }[char]));
    }

    function speak(text) {
      if (activeChannel !== "voice_chat" || !("speechSynthesis" in window)) return;
      const plainText = text.replace(/\\*\\*(.*?)\\*\\*/g, "$1").replace(/\\*(.*?)\\*/g, "$1");
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(new SpeechSynthesisUtterance(plainText));
    }

    function setMode(channel) {
      activeChannel = channel;
      const isVoice = channel === "voice_chat";
      webChatMode.classList.toggle("active", !isVoice);
      voiceChatMode.classList.toggle("active", isVoice);
      webChatMode.setAttribute("aria-pressed", String(!isVoice));
      voiceChatMode.setAttribute("aria-pressed", String(isVoice));
      voiceButton.hidden = !isVoice;
      input.placeholder = isVoice
        ? "Click the microphone or type your Bookly support request"
        : "Ask about an order, return, refund, shipping, or password reset";
      if (!isVoice) {
        if (isListening && recognition) recognition.stop();
        window.speechSynthesis?.cancel();
        voiceStatus.textContent = "Web chat is selected.";
        return;
      }
      voiceStatus.textContent = recognition
        ? "Voice chat is selected. Click the microphone to speak."
        : "Voice input is unavailable in this browser. You can still type in voice mode.";
    }

    async function sendMessage(text, channel = activeChannel) {
      addMessage("user", text);
      input.value = "";
      const res = await fetch("/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({session_id: sessionId, message: text, channel})
      });
      const data = await res.json();
      addMessage("agent", data.response);
      renderTrace(data.trace);
      speak(data.response);
    }

    form.addEventListener("submit", event => {
      event.preventDefault();
      const text = input.value.trim();
      if (text) sendMessage(text);
    });

    document.querySelector("#reset").addEventListener("click", async () => {
      await fetch("/reset", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({session_id: sessionId})
      });
      chat.innerHTML = "";
      trace.innerHTML = "";
      window.speechSynthesis?.cancel();
      addMessage("agent", "Hi, I’m Bookly’s support agent. I can check order status, start returns, and answer policy questions.");
    });

    webChatMode.addEventListener("click", () => setMode("web_chat"));
    voiceChatMode.addEventListener("click", () => setMode("voice_chat"));

    voiceButton.addEventListener("click", () => {
      if (!recognition) {
        voiceStatus.textContent = "Voice input is unavailable in this browser. You can still type.";
        input.focus();
        return;
      }
      if (isListening) {
        recognition.stop();
        return;
      }
      recognition.start();
    });

    document.querySelectorAll("[data-example]").forEach(button => {
      button.addEventListener("click", () => {
        input.value = button.dataset.example;
        input.focus();
      });
    });

    addMessage("agent", "Hi, I’m Bookly’s support agent. I can check order status, start returns, and answer policy questions.");
    setMode("web_chat");
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if urlparse(self.path).path != "/":
            self._send_json({"error": "not_found"}, status=404)
            return
        body = HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        payload = self._read_json()
        session_id = payload.get("session_id") or str(uuid4())

        if path == "/reset":
            sessions.pop(session_id, None)
            self._send_json({"ok": True})
            return

        if path != "/chat":
            self._send_json({"error": "not_found"}, status=404)
            return

        message = str(payload.get("message", "")).strip()
        if not message:
            self._send_json({"error": "message_required"}, status=400)
            return

        channel = str(payload.get("channel", "web_chat")).strip().lower()
        if channel not in {"web_chat", "voice_chat"}:
            channel = "web_chat"

        state = sessions.get(session_id, AgentState())
        result = agent.handle(message, state, channel=channel)
        sessions[session_id] = result.state
        self._send_json({"response": result.response, "trace": result.trace})

    def log_message(self, format: str, *args: object) -> None:
        return

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Bookly support agent running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
