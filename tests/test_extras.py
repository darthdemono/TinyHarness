import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from fake_server import start
from tinyharness import cli, extras


def test_calculator_evaluates_and_refuses_everything_else():
    assert extras.calculator("(3 + 4) * 2.5") == 17.5
    assert extras.calculator("-2 ** 2") == -4 and extras.calculator("7 // 2 + 7 % 4") == 6
    for bad in ("__import__('os').system('x')", "2 ** 1000", "abs(-1)", "True + 1", "'a' * 3"):
        with pytest.raises((ValueError, SyntaxError)):
            extras.calculator(bad)


def test_page_text_skips_scripts_and_styles():
    html = "<html><style>p{}</style><body><h1>Hi</h1><script>x()</script><p>there <b>you</b></p></body></html>"
    assert extras.page_text(html) == "Hi\nthere\nyou"


def test_fetch_url_reads_a_page_and_rejects_other_schemes():
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            body = b"<html><body><p>hello page</p></body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    assert extras.fetch_url("http://127.0.0.1:%d/" % srv.server_port) == "hello page"
    with pytest.raises(ValueError):
        extras.fetch_url("file:///etc/passwd")
    srv.shutdown()
    assert extras.now().startswith("20")


def test_cli_extras_flag_registers_three_tools(tmp_path, capsys):
    _, url = start(lambda b: {"role": "assistant", "content": ",".join(t["function"]["name"] for t in b.get("tools", []))})
    assert cli.main(["--url", url, "--skills", str(tmp_path), "--extras", "run", "hi"]) == 0
    assert capsys.readouterr().out.strip() == "calculator,now,fetch_url"
