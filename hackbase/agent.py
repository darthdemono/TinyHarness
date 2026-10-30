"""Tool-calling loop. Register plain functions; the loop runs them until the model answers."""
import inspect
import json

_TYPES = {int: "integer", float: "number", bool: "boolean"}


class Agent:
    def __init__(self, client, system="", skills=None, max_steps=8):
        self.client = client
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

    def run(self, prompt, images=None):
        self.messages.append({"role": "user", "content": prompt, **({"images": images} if images else {})})
        for _ in range(self.max_steps):
            msg = self.client.chat(self.messages, tools=self._schema() or None)
            self.messages.append(msg)
            calls = msg.get("tool_calls")
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
                self.messages.append({"role": "tool", "content": res, "tool_call_id": c.get("id", ""), "name": f["name"]})
        return "stopped after %d steps" % self.max_steps
