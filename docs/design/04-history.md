# History

## Timeline

All work happened on 2026-10-30 and the day before the event, in iterations. Each iteration was a branch off the previous
one, committed in small groups with one plain sentence per commit.

| Iteration | What it added |
|---|---|
| 1 | Project scaffold (named hackbase), licence, lint and type config, CI, fourteen problem statements for the event theme, chat client, skill loader, tool-calling loop, web UI and command |
| 2 | JSON-text tool calls for models without tool support; sandboxed folder tools; model bench; examples; readme |
| 3 | Layers for breadth: structured JSON output, map-reduce digest, grounded answers, skill validation, presets and saved sessions, extract/digest/ask commands, prompt-injection sweep, seven more skills, per-tab web sessions |
| 4 | Token streaming in the client, terminal and browser |
| 5 | Renamed to TinyHarness; llama.cpp manager (download, checksum, run), hardware probe, GPU and offline flags, context budget, packaged skills, extras tools, platform matrix in CI, readme rewrite, demo outline |
| 6 | UnENVerse vault support; published to GitHub over SSH; CI passed on all platforms |
| 7 | 100 percent test coverage with the gate in CI |
| 8 | Doxygen comments and configuration, badges, CodeQL, Scorecard, Codecov upload, docs publishing, these notes |
| 9 | Repository renamed to TinyHarness; positioned as a dependency; `tinyharness new` project template |

## Every commit (generated from `git log`)

| Commit | Date | Message |
|---|---|---|
| 95ec409 | 2026-10-30 | Set up the hackbase project with Apache licence, lint and type config, and CI |
| 085e4fd | 2026-10-30 | Add fourteen problem statements drawn from the Hacktoberfest AI belongs to everyone theme |
| 9bc825c | 2026-10-30 | Add a chat client for Ollama and OpenAI-compatible servers with image input |
| f85e71c | 2026-10-30 | Add a loader for SKILL.md folders with one bundled summarize skill |
| 3e123ca | 2026-10-30 | Add a tool-calling agent loop that exposes skills to the model |
| 71d1fc8 | 2026-10-30 | Add a one-page web chat UI and a command line to run the agent |
| c1242d3 | 2026-10-30 | Let the agent call tools through JSON text for models without native tool support |
| 204a04f | 2026-10-30 | Add sandboxed list, read and keyword search tools over a local folder |
| e64c731 | 2026-10-30 | Add a bench command that compares several models on the same prompts |
| 0a3956d | 2026-10-30 | Add alt text and letter explainer examples built on the base |
| b66bc2d | 2026-10-30 | Document the quick start, environment settings and the skill format |
| 43821ad | 2026-10-30 | Add a JSON extraction layer that validates a schema and retries on bad replies |
| f54d4ce | 2026-10-30 | Return line numbers from search and skip vendor folders when reading a repository |
| 0cba3af | 2026-10-30 | Add a map-reduce digest for long text and a grounded answer flow with citations |
| 5e686fd | 2026-10-30 | Validate skill folders against the Agent Skills specification with a skills --validate flag |
| 2cfe3c1 | 2026-10-30 | Add role presets and saved conversations selectable from the command line |
| 17dc752 | 2026-10-30 | Add extract, digest and ask commands for structured data, long text and cited answers |
| 0fd7d80 | 2026-10-30 | Add a prompt-injection sweep that reports which attacks leak a canary secret |
| 8b70267 | 2026-10-30 | Add seven ready skills for plain language, quizzes, coaching, first aid, receipts, repos and alt text |
| eff58c2 | 2026-10-30 | Give each browser tab its own conversation in the web UI and share one agent builder |
| 3665c54 | 2026-10-30 | Map each problem statement to the command that runs it and document the new layers |
| 5ee0115 | 2026-10-30 | Stream replies token by token from Ollama and OpenAI-compatible servers, including tool calls |
| 19fa732 | 2026-10-30 | Stream tokens to the terminal and the browser instead of waiting for the full reply |
| 18258cb | 2026-10-30 | Rename the project to TinyHarness across the package, command, settings and docs |
| c198df0 | 2026-10-30 | Add a llama.cpp manager that downloads and checksums the right build for each system |
| e281f08 | 2026-10-30 | Send tool calls to OpenAI-compatible servers in the typed JSON form they require |
| 4ecc97b | 2026-10-30 | Run llama.cpp as a managed local engine with GPU offload, a hardware check and setup command |
| 02d7182 | 2026-10-30 | Trim old turns and long tool output so small context windows are not overrun |
| 24c971f | 2026-10-30 | Ship the skills inside the package, print file paths the same on every system, cap local context |
| 38d6604 | 2026-10-30 | Add calculator, clock and web page tools behind an extras flag |
| 7359772 | 2026-10-30 | Test on Linux, macOS and Windows for x64 and arm64 and check the engine download on each |
| 5455b3b | 2026-10-30 | Add an offline flag so the local engine runs from the model cache without a network |
| 17282aa | 2026-10-30 | Rewrite the readme around the local engine and add a two-minute demo outline |
| 97a47c3 | 2026-10-30 | Load API keys and key pools from an UnENVerse vault without printing them |
| d322f05 | 2026-10-30 | Test the edges: bad model output, odd stream formats, session limits and failing agents |
| 680b0a1 | 2026-10-30 | Test doctor, setup, local engine, serve, chat and the full llama.cpp install and shutdown paths |
| 8e1e4a2 | 2026-10-30 | Require full branch coverage in CI and add the coverage plugin to the dev tools |
| b6069c1 | 2026-10-30 | Document every module, class and function in Doxygen style with the reasons behind each design choice |
| f9e6424 | 2026-10-30 | Add a Doxygen configuration that builds the API reference with call graphs |
| 166d2b2 | 2026-10-30 | Add CodeQL, OpenSSF Scorecard, Codecov upload, docs publishing and pinned dependency updates |
| 38d1f23 | 2026-10-30 | Add status, coverage, scorecard and platform badges to the readme |
| 62e4c31 | 2026-10-30 | Add design notes covering goals, architecture, decisions, history, evidence, traps and open items |
| f30f320 | 2026-10-30 | Explain GitHub rate limits, treat any health answer as ready, and fix two tests on Windows and macOS |
| 8137dcb | 2026-10-30 | Record the rate limit and cross-platform test traps in the design notes |
| e36f5ec | 2026-10-30 | Give the slow-start health test a generous timeout so loaded runners do not fail it |
| 6d8392d | 2026-10-30 | Record the organisers handbook rules, the Gemma API wording and the pre-built toolkit risk in the notes |
| 76768ce | 2026-10-30 | Add a new command that writes a fresh project depending on TinyHarness |
| b476a39 | 2026-10-30 | Present TinyHarness as a dependency, fix the repository name and update the design notes |

Regenerate this table with:

```
git log --reverse --format='| %h | %ad | %s |' --date=short
```
