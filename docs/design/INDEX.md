# Design notes: start here

These notes record why TinyHarness looks the way it does, what was tried, what was measured and what is
still open. They are written so that someone (or a tool) joining mid-project can get up to speed in
about ten minutes without reading the whole commit history. The README stays short on purpose and does
not link here; search the repository or the API reference for "design notes" to find this folder.

## Read in this order

| File | Read it for |
|---|---|
| [01-origin-and-goals.md](01-origin-and-goals.md) | The event, its rules and the goal that shaped every choice |
| [02-architecture.md](02-architecture.md) | Modules, data flow, the message shape, where to plug things in |
| [03-decision-log.md](03-decision-log.md) | Each significant decision with the alternatives that lost and the evidence |
| [04-history.md](04-history.md) | Timeline of the work, with a generated list of every commit |
| [05-verification.md](05-verification.md) | What was measured or tested, on which machine, and what was not |
| [06-gotchas.md](06-gotchas.md) | Traps that already cost time; read before debugging |
| [07-open-items.md](07-open-items.md) | What is unfinished, what needs a person, ideas not built |
| [08-working-here.md](08-working-here.md) | Conventions: commands, commit style, how to add a tool, skill, preset or flow |

## State of the project in ten lines

1. A pure-standard-library Python toolkit (3.11+) meant to be used as a **dependency** of an event project, not as the project itself. `tinyharness new NAME` writes a fresh project repository that depends on it. Apache 2.0.
2. It talks to models through one `Client` (llama.cpp's server, Ollama, any OpenAI-compatible service).
3. It can download and run llama.cpp itself (`--local`), with GPU offload through Vulkan (`--gpu`).
4. An `Agent` runs the tool-calling loop; tools, skills, presets, structured output and flows sit on top.
5. Front ends: the `tinyharness` command and a one-page streaming web UI.
6. 132 tests, 100 percent line and branch coverage enforced in CI; ruff and mypy clean.
7. CI runs on Linux, macOS and Windows, x64 and arm64; a separate job downloads and runs llama.cpp on each.
8. The default demo model is Gemma 4 E2B (Q4_0), verified for text, images and tool calls on an RTX 2060.
9. Secrets can come from an UnENVerse vault without being printed (`--unv`).
10. The problem statement for the event is not known in advance; `docs/PROBLEMS.md` lists sixteen guesses.

## Rules for editing these notes

- Keep facts dated and sourced. Say "not verified" when something was not.
- Add a decision to the log when you make one, including the option you rejected and why.
- Never put credentials, personal data or machine-specific paths here; the repository is public.
