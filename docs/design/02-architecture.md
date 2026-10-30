# Architecture

## Layers

```
 front ends     cli.py (command)          web.py (one-page UI, streaming)
                   |                           |
 behaviours     flows.py   structured.py   presets.py   redteam.py   bench.py
                   |             |
 agent          agent.py  <-- skills.py  tools.py  extras.py
                   |
 model access   client.py  ----HTTP---->  llama-server | Ollama | any OpenAI-compatible service
                                              ^
 engine         llamacpp.py (download, verify, run)    hw.py (what fits this machine)
```

Dependencies point downwards only. `client.py` imports nothing else from the package, which is why the tests
can replace the whole model with a 40-line fake HTTP server (`tests/fake_server.py`).

## The one message shape

Every layer uses the same dictionary, close to the OpenAI chat format:

```
{"role": "system" | "user" | "assistant" | "tool",
 "content": "text",
 "images": ["<base64>", ...],            # optional, user messages
 "tool_calls": [{"id", "function": {"name", "arguments"}}],   # optional, assistant messages
 "tool_call_id": "...", "name": "..."}   # tool results
```

`Client._wire` converts it to what each backend needs. Keep it that way: new features should not leak a
backend's format upwards.

## Request flow for `tinyharness --local --gpu run "..."`

1. `cli.main` parses arguments. `--unv` would re-run the whole command under `unv exec` first.
2. `--local` creates `llamacpp.Server`, which finds or downloads llama-server, starts it on a free port and
   waits for `/health` to return 200. The CLI then points the client at that port with the OpenAI backend.
3. `cli.run` builds an `Agent` (system prompt from `--preset`, skills, `--docs` tools, `--extras`).
4. `Agent.run` appends the message, calls `Client.chat` with streaming, executes any tool calls (errors are
   returned to the model, outputs are truncated) and repeats until a plain answer or `max_steps`.
5. Tokens are printed as they arrive. Leaving the `with` block stops llama-server.

## Where to plug things in

| You want to add | Do this |
|---|---|
| A tool for the model | A function with type annotations and a one-paragraph docstring; `agent.tool` or `agent.add_tools([...])` |
| A reusable prompt role | An entry in `presets.PRESETS` with a `{lang}` slot |
| A skill | A folder with `SKILL.md` (name equal to the folder, description); check with `tinyharness skills --validate` |
| A multi-call behaviour | A function in `flows.py` taking a `Client` |
| A command | A subparser in `cli.main` and a branch in `cli.run`; add a test in `tests/` |
| A different model server | Probably nothing: use `--backend openai --url ...` |

## Why a tool's docstring is special

The first paragraph (up to the first blank line) of a tool function's docstring is sent to the model as the
tool description. Doxygen tags (`@param`, `@return`) go after the blank line. `Agent._schema` enforces this.
