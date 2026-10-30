"""Chat client for Ollama and OpenAI-compatible servers, stdlib only."""
import base64
import json
import os
import urllib.request

OLLAMA = "ollama"
OPENAI = "openai"


def image_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


class Client:
    """backend 'ollama' (default, localhost:11434) or 'openai' (any /v1/chat/completions server)."""

    def __init__(self, model=None, backend=None, base_url=None, api_key=None, timeout=300):
        self.backend = backend or os.environ.get("HACKBASE_BACKEND", OLLAMA)
        self.model = model or os.environ.get("HACKBASE_MODEL", "gemma3")
        default = "http://localhost:11434" if self.backend == OLLAMA else "http://localhost:8000/v1"
        self.base_url = (base_url or os.environ.get("HACKBASE_URL", default)).rstrip("/")
        self.api_key = api_key or os.environ.get("HACKBASE_API_KEY", "")
        self.timeout = timeout

    def _post(self, path, body):
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
        """POST and yield non-empty decoded lines as they arrive."""
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
        """Stream a reply, calling on_token(text) per piece; return the assembled message."""
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
        """Turn {'role','content','images':[b64]} into the backend's shape."""
        if self.backend == OLLAMA:
            return messages
        out = []
        for m in messages:
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
        """Return the assistant message dict: {'role','content', optional 'tool_calls'}.

        With on_token the reply is streamed and on_token(text) is called for each piece.
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
        msgs = [{"role": "system", "content": system}] if system else []
        msgs.append({"role": "user", "content": prompt, **({"images": images} if images else {})})
        return self.chat(msgs)["content"]
