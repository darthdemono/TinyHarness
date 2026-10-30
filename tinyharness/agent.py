"""@file agent.py
@brief The tool-calling loop: keeps history, offers tools, runs them, feeds results back.

An Agent wraps a Client. Each call to Agent.run appends the user's message,
asks the model, executes any tool calls it makes, appends the results and
asks again, until the model answers in plain text or max_steps is reached.

Two tool-calling styles:

- Native (default): tools go to the server as JSON schema and calls come back structured.
- Text (`native_tools=False`): for models with no tool support. The tool list is
  described in a system message and the model replies with one JSON line,
  `{"tool": name, "args": {...}}`, which this module parses.

Small-context devices are handled by Agent.fit (drops old turns) and by capping
tool output (`max_tool_chars`).
"""
import inspect
import json

_TYPES = {int: "integer", float: "number", bool: "boolean"}


class Agent:
    """@brief A conversation with tools.

    Typical use:

    @code{.py}
    agent = Agent(Client(), system="You help with maths.")

    @agent.tool
    def add(a: int, b: int):
        # the docstring (here: "Add two numbers.") is the tool description
        return a + b

    print(agent.run("What is 2+3?"))
    @endcode

    @note A tool's docstring up to the first blank line is sent to the model as its description, so keep that first paragraph a short plain sentence. Doxygen tags belong after the blank line.
    """
    def __init__(self, client, system="", skills=None, max_steps=8, native_tools=True, max_chars=None, max_tool_chars=4000):
        """@brief Create an agent.

        @param client A tinyharness.client.Client (anything with a compatible `chat` method works, which is how tests inject fakes).
        @param system System prompt; skill descriptions are appended when skills are given.
        @param skills Mapping from tinyharness.skills.load; registers the `use_skill` tool.
        @param max_steps Upper bound on model calls per run, so a model that keeps calling tools cannot loop forever.
        @param native_tools False switches to the JSON-text tool protocol.
        @param max_chars If set, history sent to the model is trimmed to about this many characters (see fit).
        @param max_tool_chars Longest tool result kept; longer output is cut with a marker.
        """
        self.client = client
        self.max_chars = max_chars
        self.max_tool_chars = max_tool_chars
        self.native_tools = native_tools
        self.max_steps = max_steps
        self.tools = {}
        self.skills = skills or {}
        if self.skills:
            from .skills import catalog

            system += "\nSkills (call use_skill to read one):\n" + catalog(self.skills)
            self.tool(self.use_skill)
        self.messages = [{"role": "system", "content": system}] if system else []

    def use_skill(self, name: str):
        """Return the full instructions of a named skill.

        @param name Skill name from the catalog in the system prompt.
        @return The skill's body, or `"unknown skill: NAME"`.
        """
        s = self.skills.get(name)
        return s["body"] if s else "unknown skill: " + name

    def tool(self, fn):
        """@brief Register a function as a tool (usable as a decorator).

        The function name becomes the tool name, annotations become parameter types
        (int, float, bool, otherwise string) and every parameter is marked required.

        @param fn The function to expose.
        @return fn unchanged, so decoration does not alter the function.
        """
        self.tools[fn.__name__] = fn
        return fn

    def fit(self, messages):
        """@brief Trim the history to fit a small context window.

        System messages and the newest message always stay. Oldest turns are dropped
        first, and the history never starts in the middle of a tool exchange (leading
        assistant or tool messages are skipped until a user message). Images count as
        2000 characters each. A rough character budget is used instead of a tokenizer
        to stay dependency-free; the CLI sets it to 2.5 characters per context token.

        @param messages Full history.
        @return A shorter list, or the same list when max_chars is unset.
        """
        if not self.max_chars:
            return messages

        def size(m):
            """@brief Approximate size of one message in characters."""
            return len(m.get("content") or "") + len(json.dumps(m.get("tool_calls") or "")) + 2000 * len(m.get("images") or [])

        head = [m for m in messages if m["role"] == "system"]
        rest = [m for m in messages if m["role"] != "system"]
        budget = self.max_chars - sum(map(size, head))
        while len(rest) > 1 and sum(map(size, rest)) > budget:
            rest.pop(0)
            while len(rest) > 1 and rest[0]["role"] != "user":
                rest.pop(0)
        return head + rest

    def save(self, path):
        """@brief Write the conversation to a JSON file so a later run can continue it.

        @param path Destination file (overwritten).
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.messages, f, ensure_ascii=False)

    def load(self, path):
        """@brief Replace the conversation with one saved earlier.

        The current system prompt is kept and any system message in the file is ignored,
        so changing presets or skills between runs takes effect immediately.

        @param path File written by save.
        """
        with open(path, encoding="utf-8") as f:
            saved = json.load(f)
        head = [m for m in self.messages[:1] if m["role"] == "system"]
        self.messages = head + [m for m in saved if m["role"] != "system"]

    def add_tools(self, fns):
        """@brief Register several tools at once, for example the result of tinyharness.tools.folder_tools.

        @param fns Iterable of functions.
        """
        for fn in fns:
            self.tool(fn)

    def _schema(self):
        """@brief Build the OpenAI-style tool definitions sent to the model.

        @return A list of `{"type": "function", "function": {...}}` objects, one per registered tool.
        """
        out = []
        for name, fn in self.tools.items():
            params = inspect.signature(fn).parameters
            props = {p: {"type": _TYPES.get(a.annotation, "string")} for p, a in params.items()}
            out.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": " ".join((inspect.getdoc(fn) or "").split("\n\n")[0].split()),  # first paragraph only: Doxygen tags follow it
                    "parameters": {"type": "object", "properties": props, "required": list(props)},
                },
            })
        return out

    def _text_prompt(self):
        """@brief System message teaching a model without native tool support the JSON-line protocol.

        @return Instruction text listing each tool as `name(arg, arg): description`.
        """
        lines = [
            "You can call tools. To call one, reply with ONLY one JSON object on one line:",
            '{"tool": "<name>", "args": {...}}',
            "After the tool result arrives, continue. When done, answer in plain text with no JSON.",
            "Tools:",
        ]
        for f in self._schema():
            f = f["function"]
            lines.append("- %s(%s): %s" % (f["name"], ", ".join(f["parameters"]["properties"]), f["description"]))
        return "\n".join(lines)

    @staticmethod
    def _parse_text_call(content):
        """@brief Recognise a text-mode tool call in a model reply.

        Accepts a bare JSON object or one wrapped in a Markdown code fence. Anything else
        (including ordinary prose) means the model is giving its final answer.

        @param content The model's reply text.
        @return A list holding one call in the native shape, or None.
        """
        text = content.strip()
        if text.startswith("```"):
            text = text.strip("`").removeprefix("json").strip()
        try:
            obj = json.loads(text)
        except ValueError:
            return None
        if isinstance(obj, dict) and isinstance(obj.get("tool"), str):
            return [{"function": {"name": obj["tool"], "arguments": obj.get("args") or {}}}]
        return None

    def run(self, prompt, images=None, on_token=None):
        """@brief Send a user message and run the loop until the model gives a final answer.

        Each tool call is executed with the model's arguments. A tool that raises does not
        crash the run: the error text is returned to the model as the tool result so it
        can recover. Tool ids are generated when the backend gives none, because
        OpenAI-style servers match results to calls by id.

        @param prompt The user's message.
        @param images Optional base64 images attached to the message.
        @param on_token Optional streaming callback for the model's text.
        @return The final reply text, or `"stopped after N steps"` if max_steps ran out.
        """
        self.messages.append({"role": "user", "content": prompt, **({"images": images} if images else {})})
        for _ in range(self.max_steps):
            if self.native_tools:
                msg = self.client.chat(self.fit(self.messages), tools=self._schema() or None, on_token=on_token)
                calls = msg.get("tool_calls")
            else:
                extra = [{"role": "system", "content": self._text_prompt()}] if self.tools else []
                # text-mode tool calls are raw JSON, so only stream when no tools are registered
                msg = self.client.chat(extra + self.fit(self.messages), on_token=None if self.tools else on_token)
                calls = self._parse_text_call(msg.get("content", "")) if self.tools else None
            self.messages.append(msg)
            if not calls:
                return msg.get("content", "")
            for i, c in enumerate(calls):
                c.setdefault("id", "call_%d" % i)
                f = c["function"]
                args = f["arguments"]
                if isinstance(args, str):  # OpenAI servers send JSON text, Ollama sends a dict
                    args = json.loads(args or "{}")
                try:
                    res = str(self.tools[f["name"]](**args))
                    if len(res) > self.max_tool_chars:
                        res = res[: self.max_tool_chars] + "\n[truncated %d characters]" % (len(res) - self.max_tool_chars)
                except Exception as e:  # report the failure to the model instead of crashing
                    res = "error: %s" % e
                if self.native_tools:
                    self.messages.append({"role": "tool", "content": res, "tool_call_id": c["id"], "name": f["name"]})
                else:
                    self.messages.append({"role": "user", "content": "Tool result for %s: %s" % (f["name"], res)})
        return "stopped after %d steps" % self.max_steps
