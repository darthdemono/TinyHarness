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
            out = {"message": msg} if self.path == "/api/chat" else {"choices": [{"message": msg}]}
            data = json.dumps(out).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    srv.seen = seen
    return srv, "http://127.0.0.1:%d" % srv.server_port
