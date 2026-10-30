from fake_server import start
from hackbase.agent import Agent
from hackbase.client import Client


def test_tool_loop_runs_tool_then_answers():
    calls = []

    def reply(body):
        calls.append(body)
        if len(calls) == 1:
            return {"role": "assistant", "content": "", "tool_calls": [
                {"function": {"name": "add", "arguments": {"a": 2, "b": 3}}}]}
        return {"role": "assistant", "content": "5"}

    srv, url = start(reply)
    a = Agent(Client(model="m", base_url=url))

    @a.tool
    def add(a: int, b: int):
        """Add two numbers."""
        return a + b

    assert a.run("2+3?") == "5"
    assert calls[0]["tools"][0]["function"]["parameters"]["properties"]["a"]["type"] == "integer"
    assert calls[1]["messages"][-1]["content"] == "5"


def test_tool_error_goes_to_model_and_skill_tool(tmp_path):
    n = []

    def reply(body):
        n.append(body)
        if len(n) == 1:
            return {"role": "assistant", "content": "", "tool_calls": [
                {"function": {"name": "boom", "arguments": "{}"}}]}
        return {"role": "assistant", "content": "done"}

    srv, url = start(reply)
    a = Agent(Client(model="m", base_url=url), skills={"s": {"description": "d", "body": "B", "path": ""}})

    @a.tool
    def boom():
        """Fail."""
        raise ValueError("x")

    assert a.run("go") == "done"
    assert n[1]["messages"][-1]["content"] == "error: x"
    assert a.use_skill("s") == "B" and "unknown" in a.use_skill("q")


def test_text_tool_fallback_sends_no_tools_field_and_parses_json():
    seen = []

    def reply(body):
        seen.append(body)
        if len(seen) == 1:
            return {"role": "assistant", "content": '```json\n{"tool": "add", "args": {"a": 1, "b": 2}}\n```'}
        return {"role": "assistant", "content": "3"}

    _, url = start(reply)
    a = Agent(Client(model="m", base_url=url), native_tools=False)

    @a.tool
    def add(a: int, b: int):
        """Add two numbers."""
        return a + b

    assert a.run("1+2?") == "3"
    assert "tools" not in seen[0] and "add(a, b)" in seen[0]["messages"][0]["content"]
    assert seen[1]["messages"][-1]["content"] == "Tool result for add: 3"


def test_text_fallback_plain_answer_is_returned():
    _, url = start(lambda b: {"role": "assistant", "content": "just text"})
    a = Agent(Client(model="m", base_url=url), native_tools=False)
    a.tool(lambda: 1)
    assert a.run("hi") == "just text"


def test_streamed_run_runs_tool_and_streams_final_answer():
    n = []

    def reply(body):
        n.append(1)
        if len(n) == 1:
            return {"role": "assistant", "content": "", "tool_calls": [
                {"function": {"name": "add", "arguments": {"a": 2, "b": 3}}}]}
        return {"role": "assistant", "content": "the sum is five"}

    _, url = start(reply)
    a = Agent(Client(model="m", base_url=url))

    @a.tool
    def add(a: int, b: int):
        """Add two numbers."""
        return a + b

    got = []
    assert a.run("2+3?", on_token=got.append)== "the sum is five"
    assert "".join(got)== "the sum is five"
