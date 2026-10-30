from fake_server import start
from tinyharness.agent import Agent
from tinyharness.client import Client


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


def _history(a, n):
    for i in range(n):
        a.messages.append({"role": "user", "content": "q%d " % i + "x" * 100})
        a.messages.append({"role": "assistant", "content": "a%d " % i + "y" * 100})


def test_fit_drops_oldest_turns_but_keeps_system_and_newest():
    a = Agent(Client(model="m"), system="SYS", max_chars=500)
    _history(a, 10)
    a.messages.append({"role": "user", "content": "newest"})
    out = a.fit(a.messages)
    assert out[0]["content"] == "SYS" and out[-1]["content"] == "newest"
    assert out[1]["role"] == "user" and len(out) < len(a.messages)
    assert sum(len(m["content"]) for m in out) <= 500 + len("newest")


def test_fit_never_starts_mid_tool_call_and_is_off_by_default():
    a = Agent(Client(model="m"), max_chars=300)
    a.messages += [
        {"role": "user", "content": "x" * 200},
        {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "t", "arguments": {}}}]},
        {"role": "tool", "content": "r" * 200},
        {"role": "assistant", "content": "done"},
        {"role": "user", "content": "next"},
    ]
    out = a.fit(a.messages)
    assert [m["content"] for m in out] == ["next"]
    b = Agent(Client(model="m"))
    b.messages += a.messages
    assert b.fit(b.messages) == b.messages


def test_long_tool_result_is_truncated():
    n = []

    def reply(body):
        n.append(body)
        if len(n) == 1:
            return {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "big", "arguments": {}}}]}
        return {"role": "assistant", "content": "ok"}

    _, url = start(reply)
    a = Agent(Client(model="m", base_url=url), max_tool_chars=10)

    @a.tool
    def big():
        """Return a lot of text."""
        return "z" * 50

    a.run("go")
    assert n[1]["messages"][-1]["content"] == "z" * 10 + "\n[truncated 40 characters]"


def test_tool_description_is_the_first_paragraph_only():
    a = Agent(Client(model="m"))

    @a.tool
    def f(x: int):
        """Do the thing
        across two lines.

        @param x documentation for people, not for the model
        @return nothing
        """

    desc = a._schema()[0]["function"]["description"]
    assert desc == "Do the thing across two lines." and "@param" not in desc
