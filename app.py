from __future__ import annotations

import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from uuid import uuid4

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)
except ImportError:
    pass  # dotenv optional; fall back to real environment variables

from bookly_agent.orchestrator import AgentState, BooklySupportAgent
from bookly_agent.llm_agent import BooklyLLMAgent
from bookly_agent.voice_providers import deepgram_transcribe, elevenlabs_speak


HOST = "127.0.0.1"
PORT = 8000

agent = BooklySupportAgent()
llm_agent = BooklyLLMAgent()
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
    .pill.latency { background: #6d28d9; }
    .latency-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 4px 10px;
      margin-top: 6px;
    }
    .latency-row { display: flex; justify-content: space-between; font-size: 12px; }
    .latency-label { color: var(--muted); }
    .latency-value { font-weight: 700; font-variant-numeric: tabular-nums; }
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
          <div class="subtitle">Web chat (V1) · Browser voice (V2) · Enterprise voice via Deepgram, Anthropic &amp; ElevenLabs (V3)</div>
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
            Voice chat (Free)
          </button>
          <button id="voice-chat-enterprise-mode" class="mode-button voice" type="button" aria-pressed="false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
              <path d="M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3Z"></path>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
              <path d="M12 19v3"></path>
            </svg>
            Voice chat (Enterprise)
          </button>
        </div>
        <div id="voice-status" class="voice-status">Web chat is selected.</div>
      </div>
      <div id="mic-selector-bar" style="display:none; padding: 6px 24px 10px; gap: 8px; align-items: center; display: none; flex-wrap: wrap;">
        <label for="mic-select" style="font-size:13px; color: var(--muted); white-space: nowrap;">Microphone:</label>
        <select id="mic-select" style="flex:1; min-width:0; font: inherit; font-size:13px; border:1px solid var(--line); border-radius:6px; padding: 5px 8px; background:#fff; color: var(--ink);"></select>
      </div>
      <form id="form">
        <input id="audio-file" type="file" accept="audio/*" hidden>
        <button id="upload-audio" class="icon" type="button" aria-label="Upload audio file" title="Upload audio file instead of recording" hidden>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
          </svg>
        </button>
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
    const voiceChatEnterpriseMode = document.querySelector("#voice-chat-enterprise-mode");
    const voiceButton = document.querySelector("#voice");
    const uploadButton = document.querySelector("#upload-audio");
    const audioFileInput = document.querySelector("#audio-file");
    const voiceStatus = document.querySelector("#voice-status");
    const micSelectorBar = document.querySelector("#mic-selector-bar");
    const micSelect = document.querySelector("#mic-select");

    async function populateMicList() {
      // getUserMedia first so macOS reveals device labels
      try { await navigator.mediaDevices.getUserMedia({ audio: true }); } catch (_) {}
      const devices = await navigator.mediaDevices.enumerateDevices();
      const inputs = devices.filter(d => d.kind === "audioinput");
      micSelect.innerHTML = "";
      inputs.forEach((d, i) => {
        const opt = document.createElement("option");
        opt.value = d.deviceId;
        opt.textContent = d.label || `Microphone ${i + 1}`;
        micSelect.appendChild(opt);
      });
      if (inputs.length === 0) {
        voiceStatus.textContent = "No microphone found. Please connect one and retry.";
      }
    }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = SpeechRecognition ? new SpeechRecognition() : null;
    let activeChannel = "web_chat";
    let isListening = false;
    let mediaRecorder = null;
    let audioChunks = [];
    let isRecording = false;

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
        if (step.type === "latency") {
          const d = step.details;
          node.innerHTML = `
            <div class="step-top">
              <span class="pill latency">${step.type}</span>
              <span class="step-name">${step.name}</span>
            </div>
            <div class="latency-grid">
              <div class="latency-row"><span class="latency-label">STT (Deepgram)</span><span class="latency-value">${d.stt_deepgram_ms} ms</span></div>
              <div class="latency-row"><span class="latency-label">LLM (Anthropic)</span><span class="latency-value">${d.agent_ms} ms</span></div>
              <div class="latency-row"><span class="latency-label">TTS (ElevenLabs)</span><span class="latency-value">${d.tts_elevenlabs_ms} ms</span></div>
              <div class="latency-row"><span class="latency-label">Server total</span><span class="latency-value">${d.server_total_ms} ms</span></div>
              <div class="latency-row"><span class="latency-label">E2E (browser)</span><span class="latency-value" id="e2e-latency">—</span></div>
              <div class="latency-row"><span class="latency-label">Audio</span><span class="latency-value">${(d.audio_bytes/1024).toFixed(1)} KB</span></div>
            </div>`;
        } else {
          node.innerHTML = `
            <div class="step-top">
              <span class="pill">${step.type}</span>
              <span class="step-name">${step.name}</span>
            </div>
            <pre>${escapeHtml(JSON.stringify(step.details, null, 2))}</pre>`;
        }
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
      const isEnterprise = channel === "voice_chat_enterprise";
      webChatMode.classList.toggle("active", channel === "web_chat");
      voiceChatMode.classList.toggle("active", channel === "voice_chat");
      voiceChatEnterpriseMode.classList.toggle("active", channel === "voice_chat_enterprise");
      webChatMode.setAttribute("aria-pressed", String(channel === "web_chat"));
      voiceChatMode.setAttribute("aria-pressed", String(channel === "voice_chat"));
      voiceChatEnterpriseMode.setAttribute("aria-pressed", String(channel === "voice_chat_enterprise"));
      voiceButton.hidden = !(isVoice || isEnterprise);
      uploadButton.hidden = !isEnterprise;
      input.placeholder = (isVoice || isEnterprise)
        ? "Click the microphone or type your Bookly support request"
        : "Ask about an order, return, refund, shipping, or password reset";
      if (!isVoice && !isEnterprise) {
        if (isListening && recognition) recognition.stop();
        window.speechSynthesis?.cancel();
        micSelectorBar.style.display = "none";
        voiceStatus.textContent = "Web chat is selected.";
        return;
      }
      if (isEnterprise) {
        micSelectorBar.style.display = "flex";
        populateMicList();
      } else {
        micSelectorBar.style.display = "none";
      }
      voiceStatus.textContent = recognition
        ? (isEnterprise ? "Enterprise voice chat is selected. Select your mic then click the microphone to speak." : "Voice chat is selected. Click the microphone to speak.")
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

    let activeStream = null;

    async function startRecording() {
      if (!navigator.mediaDevices || !window.MediaRecorder) {
        voiceStatus.textContent = "Enterprise voice input is unavailable in this browser.";
        return;
      }
      try {
        const deviceId = micSelect.value;
        const audioConstraints = deviceId
          ? { audio: { deviceId: { exact: deviceId } } }
          : { audio: true };
        activeStream = await navigator.mediaDevices.getUserMedia(audioConstraints);
        const track = activeStream.getAudioTracks()[0];
        // Negotiate an audio-only MIME type Deepgram supports; avoid video/webm default on Chrome
        const preferredTypes = [
          "audio/webm;codecs=opus",
          "audio/webm",
          "audio/ogg;codecs=opus",
          "audio/ogg",
          "audio/mp4",
        ];
        const mimeType = preferredTypes.find(t => MediaRecorder.isTypeSupported(t)) || "";
        mediaRecorder = mimeType
          ? new MediaRecorder(activeStream, { mimeType })
          : new MediaRecorder(activeStream);
        const actualMimeType = mediaRecorder.mimeType || mimeType || "audio/webm";
        console.log("[V3] recording with mimeType:", actualMimeType);
        audioChunks = [];
        mediaRecorder.ondataavailable = event => {
          if (event.data.size > 0) audioChunks.push(event.data);
        };
        mediaRecorder.onstop = async () => {
          activeStream.getTracks().forEach(t => t.stop());
          activeStream = null;
          try {
            const audioBlob = new Blob(audioChunks, { type: actualMimeType });
            const arrayBuffer = await audioBlob.arrayBuffer();
            const bytes = new Uint8Array(arrayBuffer);
            let binary = '';
            for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
            const audioBase64 = btoa(binary);
            voiceStatus.textContent = "Transcribing...";
            const res = await fetch("/api/v3/audio", {
              method: "POST",
              headers: { "Content-Type": "application/json", "X-Session-Id": sessionId },
              body: JSON.stringify({ audio_base64: audioBase64, mime_type: actualMimeType })
            });
            const data = await res.json();
            if (data.error) {
              voiceStatus.textContent = `Error: ${data.error}`;
              return;
            }
            addMessage("user", data.transcript);
            addMessage("agent", data.response);
            renderTrace(data.trace);
            if (data.response_audio_base64) {
              const audio = new Audio("data:audio/mp3;base64," + data.response_audio_base64);
              audio.addEventListener("play", () => {
                if (t_mic_stop !== null) {
                  const e2e = Math.round(performance.now() - t_mic_stop);
                  const e2eEl = document.getElementById("e2e-latency");
                  if (e2eEl) e2eEl.textContent = `${e2e} ms`;
                  console.log(`[V3] E2E latency (mic stop → audio play): ${e2e}ms`);
                  t_mic_stop = null;
                }
              });
              audio.play();
            }
            voiceStatus.textContent = "Enterprise voice chat is selected. Click the microphone to speak.";
          } catch (err) {
            voiceStatus.textContent = `Error: ${err.message}`;
          }
        };
        mediaRecorder.start();
        isRecording = true;
        voiceButton.classList.add("active");
        voiceButton.setAttribute("aria-label", "Stop voice input");
        voiceButton.title = "Stop voice input";
        voiceStatus.textContent = "Recording... Click mic to stop.";
      } catch (err) {
        voiceStatus.textContent = `Microphone error: ${err.message}`;
      }
    }

    let t_mic_stop = null;

    function stopRecording() {
      if (mediaRecorder && isRecording) {
        t_mic_stop = performance.now();
        mediaRecorder.stop();
        isRecording = false;
        voiceButton.classList.remove("active");
        voiceButton.setAttribute("aria-label", "Start voice input");
        voiceButton.title = "Start voice input";
        voiceStatus.textContent = "Processing...";
      }
    }

    voiceButton.addEventListener("click", () => {
      if (activeChannel === "voice_chat_enterprise") {
        if (isRecording) {
          stopRecording();
        } else {
          startRecording();
        }
        return;
      }
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

    uploadButton.addEventListener("click", () => audioFileInput.click());

    audioFileInput.addEventListener("change", async () => {
      const file = audioFileInput.files[0];
      if (!file) return;
      audioFileInput.value = "";
      voiceStatus.textContent = "Uploading & transcribing...";
      try {
        const arrayBuffer = await file.arrayBuffer();
        const bytes = new Uint8Array(arrayBuffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
        const audioBase64 = btoa(binary);
        const res = await fetch("/api/v3/audio", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Session-Id": sessionId },
          body: JSON.stringify({ audio_base64: audioBase64, mime_type: file.type || "audio/webm" })
        });
        const data = await res.json();
        if (data.error) { voiceStatus.textContent = `Error: ${data.error}`; return; }
        addMessage("user", data.transcript);
        addMessage("agent", data.response);
        renderTrace(data.trace);
        if (data.response_audio_base64) {
          new Audio("data:audio/mp3;base64," + data.response_audio_base64).play();
        }
        voiceStatus.textContent = "Enterprise voice chat is selected. Select your mic then click the microphone to speak.";
      } catch (err) {
        voiceStatus.textContent = `Error: ${err.message}`;
      }
    });

    form.addEventListener("submit", event => {
      event.preventDefault();
      const text = input.value.trim();
      if (!text) return;
      sendMessage(text);
    });

    document.querySelector("#reset").addEventListener("click", async () => {
      const res = await fetch("/reset", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({session_id: sessionId})
      });
      if (res.ok) {
        chat.innerHTML = "";
        trace.innerHTML = "";
        sessionId = crypto.randomUUID();
        localStorage.setItem("bookly_session_id", sessionId);
        addMessage("agent", "Hi, I’m Bookly’s support agent. I can check order status, start returns, and answer policy questions.");
      }
    });

    webChatMode.addEventListener("click", () => setMode("web_chat"));
    voiceChatMode.addEventListener("click", () => setMode("voice_chat"));
    voiceChatEnterpriseMode.addEventListener("click", () => setMode("voice_chat_enterprise"));

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


def check_v3_env():
    """Check that required V3 API keys are set for enterprise voice mode."""
    missing = []
    if not os.environ.get("DEEPGRAM_API_KEY"):
        missing.append("DEEPGRAM_API_KEY")
    if not os.environ.get("ELEVENLABS_API_KEY"):
        missing.append("ELEVENLABS_API_KEY")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY")
    if missing:
        raise RuntimeError(f"Missing required V3 API keys: {', '.join(missing)}")


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
        if path == "/api/v3/audio":
            # Handle audio upload for V3 enterprise voice chat
            content_type = self.headers.get("Content-Type", "")
            if "multipart/form-data" in content_type:
                # Parse multipart form data
                import cgi
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={
                        'REQUEST_METHOD': 'POST',
                        'CONTENT_TYPE': self.headers['Content-Type'],
                    }
                )
                audio_file = form['audio'] if 'audio' in form else None
                if not audio_file or not audio_file.file:
                    self._send_json({"error": "audio_file_required"}, status=400)
                    return
                audio_bytes = audio_file.file.read()
            else:
                # Accept base64-encoded audio in JSON
                payload = self._read_json()
                audio_b64 = payload.get("audio_base64")
                mime_type = payload.get("mime_type", "audio/webm")
                import base64
                if not audio_b64:
                    self._send_json({"error": "audio_base64_required"}, status=400)
                    return
                try:
                    audio_bytes = base64.b64decode(audio_b64)
                except Exception:
                    self._send_json({"error": "invalid_audio_base64"}, status=400)
                    return
            # Check V3 env
            try:
                check_v3_env()
            except RuntimeError as e:
                self._send_json({"error": str(e)}, status=500)
                return
            # Transcribe audio (STT)
            print(f"[V3] audio size={len(audio_bytes)}B mime_type={mime_type!r}")
            t_total_start = time.perf_counter()
            try:
                t0 = time.perf_counter()
                transcript = deepgram_transcribe(audio_bytes, mime_type=mime_type)
                t_stt_ms = round((time.perf_counter() - t0) * 1000)
            except Exception as e:
                self._send_json({"error": f"Transcription failed: {e}"}, status=502)
                return
            print(f"[V3] transcript={transcript!r}  stt={t_stt_ms}ms")
            if not transcript.strip():
                self._send_json({"error": "Could not hear anything. Please speak clearly and try again."}, status=422)
                return
            # Run LLM agent (V3 uses OpenAI)
            session_id = self.headers.get("X-Session-Id") or str(uuid4())
            state = sessions.get(session_id, AgentState())
            t0 = time.perf_counter()
            result = llm_agent.handle(transcript, state, channel="voice_chat_enterprise")
            t_agent_ms = round((time.perf_counter() - t0) * 1000)
            sessions[session_id] = result.state
            # Synthesize response audio (TTS)
            try:
                t0 = time.perf_counter()
                response_audio = elevenlabs_speak(result.response)
                t_tts_ms = round((time.perf_counter() - t0) * 1000)
            except Exception as e:
                self._send_json({"error": f"Speech synthesis failed: {e}"}, status=502)
                return
            t_server_ms = round((time.perf_counter() - t_total_start) * 1000)
            print(
                f"[V3] STT={t_stt_ms}ms  "
                f"LLM(Anthropic)={t_agent_ms}ms  "
                f"TTS={t_tts_ms}ms  "
                f"Server total={t_server_ms}ms"
            )
            # Append latency step to trace so it appears in the UI panel
            result.trace.append({
                "type": "latency",
                "name": "pipeline_timing",
                "details": {
                    "stt_deepgram_ms": t_stt_ms,
                    "agent_ms": t_agent_ms,
                    "tts_elevenlabs_ms": t_tts_ms,
                    "server_total_ms": t_server_ms,
                    "audio_bytes": len(audio_bytes),
                }
            })
            response_audio_b64 = base64.b64encode(response_audio).decode("utf-8")
            self._send_json({
                "transcript": transcript,
                "response": result.response,
                "response_audio_base64": response_audio_b64,
                "trace": result.trace
            })
            return
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
        if channel not in {"web_chat", "voice_chat", "voice_chat_enterprise"}:
            channel = "web_chat"

        # V3: Check API keys before using enterprise voice
        if channel == "voice_chat_enterprise":
            try:
                check_v3_env()
            except RuntimeError as e:
                self._send_json({"error": str(e)}, status=500)
                return
            # Example usage (not wired to UI):
            # transcript = deepgram_transcribe("audio.wav")
            # audio_bytes = elevenlabs_speak("Hello from ElevenLabs!")

        # In future: route to pluggable STT/TTS provider based on channel and config
        # Example: if channel == "voice_chat_enterprise":
        #     stt_provider = get_stt_provider()  # e.g., Deepgram, OpenAI, LiveKit, etc.
        #     tts_provider = get_tts_provider()  # e.g., ElevenLabs, OpenAI, LiveKit, etc.
        #     # Call provider-specific logic here
        # For now, all channels use the same agent logic

        state = sessions.get(session_id, AgentState())
        if channel == "voice_chat_enterprise":
            result = llm_agent.handle(message, state, channel=channel)
        else:
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
    dg  = os.environ.get("DEEPGRAM_API_KEY", "")
    el  = os.environ.get("ELEVENLABS_API_KEY", "")
    ant = os.environ.get("ANTHROPIC_API_KEY", "")
    print(f"DEEPGRAM_API_KEY   : {'set (' + dg[:8]  + '...)' if dg  else 'NOT SET — V3 will fail'}")
    print(f"ELEVENLABS_API_KEY : {'set (' + el[:8]  + '...)' if el  else 'NOT SET — V3 will fail'}")
    print(f"ANTHROPIC_API_KEY  : {'set (' + ant[:8] + '...)' if ant else 'NOT SET — V3 will fail'}")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Bookly support agent running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
