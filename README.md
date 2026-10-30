# TinyHarness <a href="https://scorecard.dev/viewer/?uri=github.com/darthdemono/TinyHarness"><img src="https://img.shields.io/ossf-scorecard/github.com/darthdemono/TinyHarness?style=for-the-badge&labelColor=323330&logoColor=white&logo=openssf&label=Scorecard%20%28out%20of%2010%29" alt="OpenSSF Scorecard"></a>

<p align="center">
  <a href="https://github.com/darthdemono/TinyHarness/actions/workflows/check.yml"><img src="https://img.shields.io/github/actions/workflow/status/darthdemono/TinyHarness/check.yml?branch=main&style=for-the-badge&labelColor=323330&logoColor=white&logo=github&label=Build%20and%20tests" alt="Build and tests"></a>
  <a href="https://github.com/darthdemono/TinyHarness/actions/workflows/codeql.yml"><img src="https://img.shields.io/github/actions/workflow/status/darthdemono/TinyHarness/codeql.yml?branch=main&style=for-the-badge&labelColor=323330&logoColor=white&logo=github&label=CodeQL%20code%20scanning" alt="CodeQL code scanning"></a>
  <a href="https://github.com/darthdemono/TinyHarness/actions/workflows/docs.yml"><img src="https://img.shields.io/github/actions/workflow/status/darthdemono/TinyHarness/docs.yml?branch=main&style=for-the-badge&labelColor=323330&logoColor=white&logo=github&label=API%20reference" alt="API reference build"></a>
  <a href="https://codecov.io/gh/darthdemono/TinyHarness"><img src="https://img.shields.io/codecov/c/github/darthdemono/TinyHarness?style=for-the-badge&labelColor=323330&logoColor=white&logo=codecov&label=Coverage" alt="Test coverage"></a>
</p>

<p align="center">
  <a href="https://www.bestpractices.dev/projects/16103"><img src="https://img.shields.io/cii/level/16103?style=for-the-badge&labelColor=323330&logoColor=white&logo=openssf&label=Best%20Practices%20level" alt="OpenSSF Best Practices level"></a>
  <a href="https://github.com/darthdemono/TinyHarness/releases/latest"><img src="https://img.shields.io/github/v/release/darthdemono/TinyHarness?display_name=tag&style=for-the-badge&labelColor=323330&logoColor=white&logo=github&label=Latest%20release" alt="Latest release"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/-Linux%20%7C%20Windows%20%7C%20macOS-%23323330.svg?style=for-the-badge&logoColor=white&logo=linux" alt="Platforms: Linux, Windows and macOS">
  <img src="https://img.shields.io/badge/-x64%20%7C%20arm64-%23323330.svg?style=for-the-badge&logoColor=white&logo=arm" alt="CPUs: x64 and arm64">
  <img src="https://img.shields.io/badge/-Python%203.11%2B-%23323330.svg?style=for-the-badge&logoColor=white&logo=python" alt="Python 3.11 and newer">
  <img src="https://img.shields.io/badge/-llama.cpp-%23323330.svg?style=for-the-badge&logoColor=white" alt="Engine: llama.cpp">
  <a href="https://github.com/darthdemono/TinyHarness/blob/main/LICENSE"><img src="https://img.shields.io/badge/-Apache--2.0-%23323330.svg?style=for-the-badge&logoColor=white&logo=apache" alt="Licence: Apache-2.0"></a>
  <a href="https://darthdemono.github.io/TinyHarness/"><img src="https://img.shields.io/badge/-API%20reference-%23323330.svg?style=for-the-badge&logoColor=white&logo=readthedocs" alt="API reference"></a>
</p>

A small, fast toolkit that other projects build on. Use it as a dependency: it supplies the model client, the
tool-calling loop, local llama.cpp, a streaming web page and a set of ready tools, so your own project contains only
what is specific to your idea. Pure Python standard library, no dependencies, Apache 2.0. Runs on Linux, macOS and
Windows, on x64 and arm64, on a laptop CPU or a small GPU.

The project is called TinyHarness; the Python package and the command are written in lowercase, `tinyharness`.

## Start your own project on top of it

```
pip install git+https://github.com/darthdemono/TinyHarness
tinyharness new my-project         # writes a new repository: licence, README, app, test, CI, submission checklist
cd my-project
pip install -e .
python app.py serve                # your assistant on http://127.0.0.1:8080
```

The new project lists TinyHarness as its only dependency, starts as its own git repository (no commit is made) and has its
own history, README and licence. Replace the system prompt in `app.py` and add tools; everything else is already wired.

## Start in five minutes

```
pip install -e .
tinyharness doctor              # shows this machine and the model that fits it
tinyharness setup               # downloads llama.cpp (checksum verified); add --variant vulkan for GPUs
tinyharness --local run "Say hello in Hungarian"
```

`--local` starts llama.cpp for the length of the command, downloads the recommended model on first use and
stops it afterwards. Useful flags:

| Flag | Effect |
|---|---|
| `--local [MODEL]` | `auto` (fits this machine), a Hugging Face spec such as `ggml-org/gemma-4-E2B-it-GGUF:Q4_0`, or a `.gguf` path |
| `--gpu` | Vulkan build, every layer on the GPU (NVIDIA, AMD, Intel) |
| `--offline` | use the cached model only, no network (do the first run at home) |
| `--ctx N` | context size; history and tool output are trimmed to fit it |
| `--threads N` | CPU threads |

Already running Ollama or any OpenAI-compatible server? Skip `--local` and use `--backend ollama|openai --url ...`
or the `TINYHARNESS_BACKEND`, `TINYHARNESS_MODEL`, `TINYHARNESS_URL`, `TINYHARNESS_API_KEY` variables.

### Measured on one machine

Intel i5-6600K (4 cores), 16 GB RAM, NVIDIA RTX 2060 6 GB, Linux, llama.cpp b12015, Gemma 4 E2B Q4_0 (2.8 GB):
about 3 tokens per second on CPU, 57 to 84 on the GPU with Vulkan; image reading and tool calls both worked.
The first run downloads the model (about 3.4 GB with the image projector); later runs start in under a minute.
Other systems are covered by the test matrix but have not been timed.

## What is in it

- `client`: chat with llama.cpp, Ollama or any OpenAI-compatible server, with image input and token streaming.
- `agent`: tool-calling loop; native tool calls, or JSON text for models without them (`--text-tools`).
- `skills`: `SKILL.md` folders per the Agent Skills spec, validated with `tinyharness skills --validate`. Eight ship with the package.
- `tools`: sandboxed list, read and keyword search over a folder (`--docs DIR`). `extras`: calculator, clock, web page text (`--extras`).
- `structured`: ask for JSON matching a schema, validated with retries; `extract` turns an image or text into JSON or CSV.
- `flows`: `digest` for long text, `ask` for answers that cite `path:line` and refuse outside the sources.
- `presets`: role prompts in any language (`--preset plain|describer|tutor|quiz|coach|firstaid|translator --lang Hungarian`).
- `redteam`: prompt-injection sweep that reports which attacks leaked a canary.
- `bench`: same prompts through several models, markdown table out.
- `web`: one-page chat UI with image upload, streaming and one conversation per tab (`tinyharness serve`).

## Commands

```
tinyharness --local chat
tinyharness --local --gpu run -i photo.jpg "What is on this sign?"
tinyharness --local --docs ./notes run "What does the permit rule say?"
tinyharness --local --extras run "What is 17 * 23? Use the calculator."
tinyharness --local extract --fields item:str,qty:int,price:float --many --csv -i receipt.jpg
tinyharness --local digest chat_export.txt
tinyharness --local ask ./textbook "Why is the sky blue?"
tinyharness --local --preset coach --lang Hungarian --session me.json chat
tinyharness --local redteam
tinyharness --local serve --port 8080
tinyharness bench --backend openai --url http://localhost:8080/v1 --models a,b "Explain DNS in two lines"
```

## Secrets from UnENVerse

For a hosted OpenAI-compatible endpoint (a fallback when there is no GPU), keep the key in an
[UnENVerse](https://github.com/darthdemono/UnENVerse) vault instead of a file or a shell variable.
`--unv` re-runs the command under `unv exec`, so the key reaches TinyHarness as `TINYHARNESS_API_KEY` in its
environment and is never printed or passed on a command line:

```
tinyharness --unv Groq --backend openai --url https://api.groq.com/openai/v1 -m MODEL run "Hello"
tinyharness --unv-pool free-keys --backend openai --url https://... -m MODEL chat   # next key from a rate-limit pool
tinyharness --unv "Hugging Face=HF_TOKEN:key" --local ggml-org/some-gated-GGUF run "Hi"
```

`--unv ENTRY` maps the entry's primary value to `TINYHARNESS_API_KEY`; write `Provider=VAR:field` to choose the variable
and field yourself. Both flags repeat. This needs the `unv` command on `PATH` and works the same on every system.

## Build your own

```python
from tinyharness.agent import Agent
from tinyharness.client import Client

agent = Agent(Client(backend="openai", base_url="http://127.0.0.1:8080/v1"), system="You help with maths.")

@agent.tool
def add(a: int, b: int):
    """Add two numbers."""
    return a + b

print(agent.run("What is 2+3?"))
```

Two worked examples are in `examples/`.

## Skills

```
my-skills/summarize/SKILL.md
---
name: summarize
description: Summarise a long text into five bullets and one takeaway line.
---
Instructions the model reads when it calls use_skill.
```

Point `--skills my-skills` at the folder. The agent lists names and descriptions in its prompt and reads a body only when it asks.

## Develop

```
pip install -e ".[dev]"
pytest -q && ruff check . && mypy tinyharness
```

Tests use a local fake server, so they need no model and no network. Licensed under Apache 2.0; see `LICENSE` and `NOTICE`.
