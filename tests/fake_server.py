"""Tiny stand-in for Ollama and OpenAI servers so tests need no model."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


def start(reply):
    """reply(body) -> message dict. Returns (server, base_url); paths ending /chat answer Ollama-style."""
    seen = []

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            seen.append((self.path, body))
            msg = reply(body)
            if body.get("stream") is True:
                return self._stream(msg)
            out = {"message": msg} if self.path == "/api/chat" else {"choices": [{"message": msg}]}
            data = json.dumps(out).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _stream(self, msg):
            """Answer in the streaming wire format of whichever backend the path belongs to."""
            words = [w + " " for w in msg.get("content", "").split()]
            lines = []
            if self.path == "/api/chat":
                lines += [json.dumps({"message": {"content": w}, "done": False}) for w in words]
                lines.append(json.dumps({"message": {"content": "", "tool_calls": msg.get("tool_calls", [])}, "done": True}))
            else:
                lines += ["data: " + json.dumps({"choices": [{"delta": {"content": w}}]}) for w in words]
                for i, c in enumerate(msg.get("tool_calls", [])):
                    f = c["function"]
                    a = f["arguments"] if isinstance(f["arguments"], str) else json.dumps(f["arguments"])
                    half = len(a) // 2
                    for part, name in ((a[:half], f["name"]), (a[half:], "")):
                        d = {"index": i, "id": "c%d" % i, "function": {"name": name, "arguments": part}}
                        lines.append("data: " + json.dumps({"choices": [{"delta": {"tool_calls": [d]}}]}))
                lines.append("data: [DONE]")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(("\n".join(lines) + "\n").encode())

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    srv.seen = seen
    return srv, "http://127.0.0.1:%d" % srv.server_port
