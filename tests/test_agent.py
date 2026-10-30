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
