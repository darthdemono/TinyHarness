"""Tool-calling loop. Register plain functions; the loop runs them until the model answers."""
import inspect
import json

_TYPES = {int: "integer", float: "number", bool: "boolean"}


class Agent:
    def __init__(self, client, system="", skills=None, max_steps=8, native_tools=True):
        self.client = client
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
        """Return the full instructions of a named skill."""
        s = self.skills.get(name)
        return s["body"] if s else "unknown skill: " + name

    def tool(self, fn):
        """Register fn. Its docstring is the description; annotations give parameter types."""
        self.tools[fn.__name__] = fn
        return fn

    def add_tools(self, fns):
        for fn in fns:
            self.tool(fn)

    def _schema(self):
        out = []
        for name, fn in self.tools.items():
            params = inspect.signature(fn).parameters
            props = {p: {"type": _TYPES.get(a.annotation, "string")} for p, a in params.items()}
            out.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": inspect.getdoc(fn) or "",
                    "parameters": {"type": "object", "properties": props, "required": list(props)},
                },
            })
        return out

    def _text_prompt(self):
        """Instructions for models with no native tool calling: reply with one JSON line."""
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
        """Return a native-shaped call list if content is a {'tool','args'} JSON object, else None."""
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

    def run(self, prompt, images=None):
        self.messages.append({"role": "user", "content": prompt, **({"images": images} if images else {})})
        for _ in range(self.max_steps):
            if self.native_tools:
                msg = self.client.chat(self.messages, tools=self._schema() or None)
                calls = msg.get("tool_calls")
            else:
                extra = [{"role": "system", "content": self._text_prompt()}] if self.tools else []
                msg = self.client.chat(extra + self.messages)
                calls = self._parse_text_call(msg.get("content", "")) if self.tools else None
            self.messages.append(msg)
            if not calls:
                return msg.get("content", "")
            for c in calls:
                f = c["function"]
                args = f["arguments"]
                if isinstance(args, str):  # OpenAI servers send JSON text, Ollama sends a dict
                    args = json.loads(args or "{}")
                try:
                    res = str(self.tools[f["name"]](**args))
                except Exception as e:  # report the failure to the model instead of crashing
                    res = "error: %s" % e
                if self.native_tools:
                    self.messages.append({"role": "tool", "content": res, "tool_call_id": c.get("id", ""), "name": f["name"]})
                else:
                    self.messages.append({"role": "user", "content": "Tool result for %s: %s" % (f["name"], res)})
        return "stopped after %d steps" % self.max_steps
