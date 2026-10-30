# Getting started

This guide covers installation, everyday use and the security points to know before you run TinyHarness. The full command list is in the
[README](../README.md); every module, class and function is in the generated API reference.

## Installation

TinyHarness needs Python 3.11 or newer and has no other dependency.

```
pip install git+https://github.com/darthdemono/TinyHarness      # as a dependency of your own project
pip install -e ".[dev]"                                          # from a clone, with the test and lint tools
```

Check what the machine can run, then fetch the local engine once (llama.cpp, checksum verified):

```
tinyharness doctor
tinyharness setup                  # add --variant vulkan for a GPU build
```

## Using it

```
tinyharness --local run "Say hello in Hungarian"          # starts the engine, downloads the model on first use, stops it afterwards
tinyharness --local --gpu --offline chat                  # GPU offload, model from the cache, no network
tinyharness --local --docs ./notes run "What does the rule say?"
tinyharness --local extract --fields item:str,price:float --many --csv -i receipt.jpg
tinyharness --local ask ./textbook "Why is the sky blue?"  # answers only from the folder, with citations
tinyharness --local serve                                   # one-page chat on http://127.0.0.1:8080
```

Global flags such as `--local`, `--gpu`, `--docs` and `--preset` come before the subcommand. To use another model server, leave out
`--local` and pass `--backend ollama|openai --url ...`; `TINYHARNESS_BACKEND`, `TINYHARNESS_MODEL`, `TINYHARNESS_URL` and
`TINYHARNESS_API_KEY` set the same things.

As a library:

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

To start a new project that depends on TinyHarness, run `tinyharness new my-project`.

## Security

- API keys come from the environment or an UnENVerse vault (`--unv`); they are never printed or placed on a command line. Do not paste keys
  into issues.
- The chat page listens on 127.0.0.1 only and has no login. Do not expose it on a network.
- Give an agent only the tools it needs. `fetch_url` can read any address the machine can reach, and a model can be tricked by text it reads
  (prompt injection). `tinyharness redteam` tests one narrow case.
- The engine download is checked against the SHA-256 digest GitHub publishes for the release asset before it is unpacked.
- Report vulnerabilities privately; see [SECURITY.md](../SECURITY.md). The threat model is in [THREAT_MODEL.md](../THREAT_MODEL.md).

## More

[Design notes](design/INDEX.md) explain why it is built this way, with decisions, history, evidence and known traps.
