from fake_server import start
from tinyharness.client import Client


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


def test_stream_ollama_collects_tokens_and_tool_calls():
    call = {"function": {"name": "add", "arguments": {"a": 1}}}
    _, url = start(lambda b: {"role": "assistant", "content": "hello big world", "tool_calls": [call]})
    got = []
    msg = Client(model="m", backend="ollama", base_url=url).chat([{"role": "user", "content": "x"}], on_token=got.append)
    assert "".join(got) == "hello big world" and msg["content"] == "hello big world"
    assert msg["tool_calls"] == [call]


def test_stream_openai_assembles_fragmented_tool_call():
    call = {"function": {"name": "add", "arguments": '{"a": 1, "b": 2}'}}
    _, url = start(lambda b: {"role": "assistant", "content": "ok", "tool_calls": [call]})
    msg = Client(model="m", backend="openai", base_url=url).chat([{"role": "user", "content": "x"}], on_token=lambda t: None)
    assert msg["content"] == "ok"
    assert msg["tool_calls"][0]["function"] == {"name": "add", "arguments": '{"a": 1, "b": 2}'}
    assert msg["tool_calls"][0]["id"] == "c0"


def test_openai_history_gets_typed_json_text_tool_calls():
    srv, url = start(lambda b: {"role": "assistant", "content": "ok"})
    msgs = [
        {"role": "user", "content": "q"},
        {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "add", "arguments": {"a": 1}}}]},
        {"role": "tool", "content": "1", "tool_call_id": "call_0", "name": "add"},
    ]
    Client(model="m", backend="openai", base_url=url).chat(msgs)
    call = srv.seen[0][1]["messages"][1]["tool_calls"][0]
    assert call == {"id": "call_0", "type": "function", "function": {"name": "add", "arguments": '{"a": 1}'}}
