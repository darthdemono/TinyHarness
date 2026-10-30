from fake_server import start
from hackbase.client import Client


def test_ollama_ask_with_image():
    srv, url = start(lambda b: {"role": "assistant", "content": "hi"})
    c = Client(model="m", backend="ollama", base_url=url)
    assert c.ask("q", images=["QUJD"]) == "hi"
    path, body = srv.seen[0]
    assert path == "/api/chat" and body["stream"] is False
    assert body["messages"][0]["images"] == ["QUJD"]


def test_openai_image_becomes_data_url():
    srv, url = start(lambda b: {"role": "assistant", "content": "ok"})
    c = Client(model="m", backend="openai", base_url=url, api_key="k")
    assert c.ask("q", images=["QUJD"]) == "ok"
    path, body = srv.seen[0]
    assert path == "/chat/completions"
    assert body["messages"][0]["content"][1]["image_url"]["url"].endswith("QUJD")
