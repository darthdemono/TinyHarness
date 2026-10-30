# hackbase

Zero-dependency starter kit for open-weight AI hack day projects. Pure Python standard library, Python 3.11 or newer.

## Parts

- `hackbase.client`: chat with Ollama or any OpenAI-compatible server, with image input.
- `hackbase.skills`: load `SKILL.md` folders (name and description frontmatter).
- `hackbase.agent`: tool-calling loop. Native tool calls by default, JSON text fallback for models without them.
- `hackbase.tools`: sandboxed list, read and keyword search over a local folder.
- `hackbase.structured`: ask for JSON matching a schema, validated with retries; CSV export. Image in, table out.
- `hackbase.flows`: map-reduce `digest` of long text, `grounded` answers that cite `path:line` and refuse outside the sources.
- `hackbase.presets`: role prompts (plain, describer, tutor, quiz, coach, firstaid, translator) in any language.
- `hackbase.redteam`: prompt-injection sweep that reports which attacks leaked a canary secret.
- `hackbase.bench`: same prompts through several models, markdown table out.
- `hackbase.web`: one-page chat UI on `http.server`, with image upload and one conversation per tab.
- `hackbase.cli`: the `hackbase` command.

## Quick start

```
pip install -e '.[dev]'
ollama pull gemma3
hackbase run "Say hello in Hungarian"
hackbase -m gemma3 run -i photo.jpg "What is on this sign?"
hackbase --docs ./notes chat
hackbase --text-tools --docs ./notes run "What does the permit rule say?"
hackbase bench --models gemma3,llama3.2 "Explain DNS in two lines"
hackbase extract --fields item:str,qty:int,price:float --many --csv -i receipt.jpg
hackbase digest chat_export.txt
hackbase ask ./textbook "Why is the sky blue?"
hackbase --preset coach --lang Hungarian --session me.json chat
hackbase redteam
hackbase skills --validate
hackbase serve --port 8080
```

Settings come from flags or the environment: `HACKBASE_BACKEND` (`ollama` or `openai`), `HACKBASE_MODEL`,
`HACKBASE_URL`, `HACKBASE_API_KEY`. For a hosted OpenAI-compatible endpoint use `--backend openai --url <base>/v1`.

## Build your own

Register any function as a tool; its docstring is the description and its annotations give the types:

```python
from hackbase.agent import Agent
from hackbase.client import Client

agent = Agent(Client(), system="You are a helpful assistant.")

@agent.tool
def add(a: int, b: int):
    """Add two numbers."""
    return a + b

print(agent.run("What is 2+3?"))
```

Two worked examples live in `examples/`: `alt_text.py` (image to alt text) and `letter_explainer.py`
(plain-language letter explainer over a local rules folder).

## Skills

A skill is a folder with a `SKILL.md`:

```
skills/summarize/SKILL.md
---
name: summarize
description: Summarise a long text into five bullets and one takeaway line.
---
Instructions the model reads when it calls use_skill.
```

The agent lists skill names and descriptions in its system prompt and reads a body only when it asks for it.

## Problem statements

`docs/PROBLEMS.md` lists fourteen ideas, each with the command that gets a first demo running.

Licensed under Apache 2.0.
