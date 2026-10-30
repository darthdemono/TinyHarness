"""@file client.py
@brief Talk to a language model over HTTP with only the standard library.

Two wire formats are supported behind one class:

- Ollama's native API (POST /api/chat, newline-delimited JSON when streaming).
- The OpenAI-compatible API (POST /chat/completions, server-sent events when
  streaming), which is what llama.cpp's llama-server, vLLM, LM Studio and most
  hosted services speak.

Everything above this module (agent loop, flows, CLI) sees one message shape
(`{"role", "content", optional "images", optional "tool_calls"}`) and never
cares which backend answered. Differences are confined to `Client._wire`
(request side) and `Client._chat_stream` (response side).
"""
import base64
import json
import os
import urllib.request

OLLAMA = "ollama"
OPENAI = "openai"


def image_b64(path):
    """@brief Read an image file and return it base64 encoded.

    Both backends take images as base64 text, so this is the one place a file
    becomes a string.

    @param path Path of the image file (any format the model accepts, usually PNG or JPEG).
    @return The file's bytes as an ASCII base64 string.
    @throws OSError If the file cannot be read.
    """
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


class Client:
    """@brief A chat connection to one model on one server.

    Configuration comes from the constructor or, when an argument is omitted,
    from the environment: TINYHARNESS_BACKEND, TINYHARNESS_MODEL,
    TINYHARNESS_URL and TINYHARNESS_API_KEY. The class holds no conversation
    state; callers pass the whole message list on every call.

    @see tinyharness.agent.Agent for the layer that keeps history and runs tools.
    """

    def __init__(self, model=None, backend=None, base_url=None, api_key=None, timeout=300):
        """@brief Create a client.

        @param model Model name sent in each request. llama-server ignores it (it serves one model); Ollama and hosted services require it.
        @param backend `"ollama"` or `"openai"`. Defaults to TINYHARNESS_BACKEND, then `"ollama"`.
        @param base_url Server root. Defaults to TINYHARNESS_URL, then localhost:11434 (Ollama) or localhost:8000/v1 (OpenAI style).
        @param api_key Bearer token for hosted services. Defaults to TINYHARNESS_API_KEY; empty means no Authorization header.
        @param timeout Seconds to wait for the server (per read, not per reply). Generous because first token from a cold local model can be slow.
        """
        self.backend = backend or os.environ.get("TINYHARNESS_BACKEND", OLLAMA)
        self.model = model or os.environ.get("TINYHARNESS_MODEL", "gemma3")
        default = "http://localhost:11434" if self.backend == OLLAMA else "http://localhost:8000/v1"
        self.base_url = (base_url or os.environ.get("TINYHARNESS_URL", default)).rstrip("/")
        self.api_key = api_key or os.environ.get("TINYHARNESS_API_KEY", "")
        self.timeout = timeout

    def _post(self, path, body):
        """@brief POST a JSON body and return the parsed JSON reply (non-streaming).

        @param path Path appended to base_url, for example `"/api/chat"`.
        @param body Request object, serialised as JSON.
        @return The decoded JSON response.
        @throws urllib.error.URLError If the server is unreachable or answers with an HTTP error.
        """
        req = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )
        if self.api_key:
            req.add_header("Authorization", "Bearer " + self.api_key)
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.load(r)

    def _lines(self, path, body):
        """@brief POST a JSON body and yield the reply one non-empty line at a time as it arrives.

        Used by streaming. Blank lines (SSE separators, NDJSON padding) are skipped here so callers only see content.

        @param path Path appended to base_url.
        @param body Request object, serialised as JSON.
        @return A generator of decoded, stripped lines.
        """
        req = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )
        if self.api_key:
            req.add_header("Authorization", "Bearer " + self.api_key)
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            for raw in r:
                line = raw.decode().strip()
                if line:
                    yield line

    def _chat_stream(self, body, on_token):
        """@brief Stream a reply and assemble it into a normal message.

        Ollama sends complete tool calls inside ordinary chunks. OpenAI-style servers
        send a tool call in fragments (name first, then pieces of the JSON arguments
        text) keyed by index, so fragments are concatenated per index and emitted as
        finished calls at the end. Argument text stays a JSON string for OpenAI style;
        the agent parses it.

        @param body Request object; `stream` is forced to true.
        @param on_token Called with each text piece as soon as it arrives.
        @return `{"role": "assistant", "content": full_text}` plus `tool_calls` when the model asked for tools.
        """
        body["stream"] = True
        content, calls = "", []
        partial = {}  # OpenAI sends tool calls in fragments keyed by index
        path = "/api/chat" if self.backend == OLLAMA else "/chat/completions"
        for line in self._lines(path, body):
            if self.backend == OLLAMA:
                m = json.loads(line).get("message", {})
                tok = m.get("content", "")
                calls += m.get("tool_calls") or []
            else:
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                delta = json.loads(data)["choices"][0]["delta"]
                tok = delta.get("content") or ""
                for tc in delta.get("tool_calls") or []:
                    p = partial.setdefault(tc["index"], {"id": "", "name": "", "arguments": ""})
                    p["id"] = tc.get("id") or p["id"]
                    f = tc.get("function") or {}
                    p["name"] += f.get("name") or ""
                    p["arguments"] += f.get("arguments") or ""
            if tok:
                content += tok
                on_token(tok)
        calls += [{"id": p["id"], "function": {"name": p["name"], "arguments": p["arguments"]}} for _, p in sorted(partial.items())]
        msg = {"role": "assistant", "content": content}
        if calls:
            msg["tool_calls"] = calls
        return msg

    def _wire(self, messages):
        """@brief Convert the shared message shape into what the chosen backend expects.

        Ollama takes our messages almost as they are. OpenAI-style servers need three changes:
        a message with `images` becomes a content list with `image_url` data URLs, and an
        assistant message with `tool_calls` must carry `"type": "function"`, a call `id`
        and the arguments as JSON text. Servers such as llama-server reject the history
        (HTTP 500, "Missing tool call type") if these are absent.

        @param messages Conversation in the shared shape.
        @return A new list in the backend's wire format; the input is not modified.
        """
        if self.backend == OLLAMA:
            return messages
        out = []
        for m in messages:
            if m.get("tool_calls"):  # OpenAI servers insist on type=function and JSON-text arguments
                calls = [
                    {
                        "id": c.get("id") or "call_%d" % i,
                        "type": "function",
                        "function": {
                            "name": c["function"]["name"],
                            "arguments": c["function"]["arguments"]
                            if isinstance(c["function"]["arguments"], str)
                            else json.dumps(c["function"]["arguments"]),
                        },
                    }
                    for i, c in enumerate(m["tool_calls"])
                ]
                out.append({**m, "tool_calls": calls})
                continue
            imgs = m.get("images")
            if not imgs:
                out.append(m)
                continue
            parts = [{"type": "text", "text": m["content"]}]
            parts += [
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + i}}
                for i in imgs
            ]
            out.append({"role": m["role"], "content": parts})
        return out

    def chat(self, messages, tools=None, on_token=None):
        """@brief Send a conversation and return the model's next message.

        @param messages Full history: system, user, assistant and tool messages in order.
        @param tools Optional OpenAI-style tool definitions the model may call.
        @param on_token If given, the reply is streamed and this callback receives each text piece.
        @return The assistant message: `role`, `content`, and `tool_calls` when tools were requested.
        @throws urllib.error.URLError On connection or HTTP failure.
        """
        body = {"model": self.model, "messages": self._wire(messages)}
        if tools:
            body["tools"] = tools
        if on_token:
            return self._chat_stream(body, on_token)
        if self.backend == OLLAMA:
            body["stream"] = False
            return self._post("/api/chat", body)["message"]
        return self._post("/chat/completions", body)["choices"][0]["message"]

    def ask(self, prompt, images=None, system=None):
        """@brief One-shot convenience: a single question, optionally with images, answered as plain text.

        @param prompt The user's question.
        @param images Optional list of base64 strings (see image_b64).
        @param system Optional system prompt placed first.
        @return The reply text.
        """
        msgs = [{"role": "system", "content": system}] if system else []
        msgs.append({"role": "user", "content": prompt, **({"images": images} if images else {})})
        return self.chat(msgs)["content"]
