# Decision log

Newest decisions last. Each entry: what was decided, what else was considered, the evidence. Dates are 2026-10-30
unless stated; most of the project was built in one long session the day before the event.

## D1. Standard library only
Chosen: no runtime dependencies (`dependencies = []`). Rejected: `requests`, `httpx`, `openai` SDK, `pydantic`.
Why: a hack day wastes minutes on installs and version clashes; arm64 Windows and old laptops make wheels a risk.
Cost: hand-written SSE/NDJSON parsing and a tiny schema checker. Both are small and fully tested.

## D2. Reuse llama.cpp instead of writing inference
Chosen: drive `llama-server` over its OpenAI-compatible HTTP API. Rejected: `llama-cpp-python` (needs a compiler
or a wheel per platform), Ollama as a hard requirement (extra install, no Vulkan on some machines), PyTorch
(heavy, slow on CPU). Ollama and any other server still work through `--backend`.

## D3. Download the engine ourselves, with a checksum
`llamacpp.install` reads the GitHub releases list, picks the asset for this OS and CPU and verifies the SHA-256
that GitHub publishes per asset. Evidence: `/releases/latest` returned a stub release (tag v0.8.0, one text file) on
2026-10-30, while real builds are prereleases named `bNNNNN`; hence the list endpoint. Asset names are matched
by regex per target and CI runs the binary on all six runner types to catch a rename.

## D4. Vulkan for GPUs, not CUDA
Chosen: `--gpu` uses the `vulkan` release build. Why: it is about 34 MB, needs only the normal graphics driver and
works on NVIDIA, AMD and Intel; the CUDA build needs a CUDA runtime bundle of several hundred MB. Evidence: an RTX 2060
(6 GB) exposes a Vulkan device and ran Gemma 4 E2B at 57 to 84 tokens per second, against about 3 on the CPU of the
same machine. CUDA might be faster; not measured.

## D5. Low-memory defaults for the engine
`-np 1` (one slot; the auto default multiplies KV-cache memory), `-ctk/-ctv q8_0` (halves KV memory), `--no-webui`,
bind to 127.0.0.1, context 4096. Flags were read from `llama-server --help` of build b12015, not remembered.

## D6. Model tiers by RAM (hw.py)
Under 3 GB RAM: Gemma 3 270M. Under 6 GB: Gemma 3 1B Q4_K_M. Under 12 GB: Gemma 4 E2B Q4_0 (text and images).
Otherwise Gemma 4 E4B Q4_0. Repositories and file sizes were checked on Hugging Face the same day. The thresholds
are a rule of thumb and were timed only on one machine.

## D7. Two tool-calling modes
Native tool calls are the default. `--text-tools` exists for models without tool support: the model replies with one
JSON line. Rejected: forcing native only, which would exclude the smallest models; grammar-constrained output, which
is engine specific.

## D8. Retries with feedback for structured output
`ask_json` validates against a flat schema and sends the exact error back (default two retries). Small models
frequently omit a key or add chatter; one retry with the error fixes most cases. A full JSON Schema validator was
rejected as a dependency and as overkill.

## D9. Retrieval is keyword search
No embeddings, no vector store. Instant, deterministic, explainable on stage, and good enough for a folder of notes.
`grounded` refuses without calling the model when nothing matches, to avoid invented answers. Upgrade path if needed:
an embeddings endpoint behind the same `search` signature.

## D10. Context budget by characters
Small devices mean small windows. `Agent.fit` drops the oldest turns until about `ctx * 2.5` characters remain, never
starting mid tool exchange; tool output is cut at 4000 characters. A tokenizer would be exact but is a dependency.

## D11. Skills follow the published specification
Frontmatter rules (name 1 to 64 lowercase letters, digits, single hyphens, equal to the folder; description 1 to 1024
characters) come from agentskills.io/specification, fetched 2026-10-30. The parser is deliberately flat; nested
YAML such as `metadata:` is not supported. Eight skills ship inside the package so they work after `pip install`.

## D12. Naming
The first name was `hackbase`. After re-reading the theme of the event it was built for, candidates were Potluck, Lifeboat, Lantern, Kindling,
Keel and Commons (checked for PyPI availability). Bedrock was dropped because it collides with a cloud AI product.
The owner chose **TinyHarness** (it also names the "model harness" prize category).

## D13. Tests use a fake server and measure behaviour
`tests/fake_server.py` speaks both wire formats, including streaming and fragmented tool calls. Expectations come from
documented behaviour, not from reading the code back. Coverage is a map of what is untested, not the goal. The CI gate
is 100 percent line and branch coverage (`fail_under = 100`), measured on Linux only; platform-specific branches are
exercised by patching `os.name` and friends so the number does not depend on the runner.

## D14. Platform matrix and the engine job
Six runners (Linux, macOS, Windows; x64 and arm64) times Python 3.11 and 3.14 for tests, plus a job per runner that
downloads llama.cpp and runs `--version`. Runner labels were checked in GitHub's documentation. All 18 jobs passed on the
first run (2026-10-30).

## D15. Secrets through the vault, never as text
`--unv ENTRY` re-runs the command under `unv exec`, which injects the secret into the child's environment. The key is
never printed or placed on a command line; the test uses a stand-in `unv` and asserts exactly that.

## D16. Documentation
Doxygen builds the API reference from docstrings. `PYTHON_DOCSTRING = NO` is required: despite the name, NO makes Doxygen
parse a Python docstring as a Doxygen comment (so `@param` works); YES prints it verbatim. Verified with a small experiment.
Design notes live in this folder and are not linked from the README by choice.

## D17. Badges and supply-chain checks
Scorecard, CodeQL, Codecov upload, pinned action SHAs and Dependabot with a one-week cooldown follow the pattern of the
owner's other repository. Codecov and the Best Practices badge need the owner's accounts; see the open items.

## D18. A dependency, not the project (owner decision, 2026-10-30)
TinyHarness is treated as an ordinary open-source dependency that speeds up whatever project is built on it. A project is started with
`tinyharness new` (module `scaffold.py`): a separate repository with its own idea, code, tests, README, licence and history, listing `tinyharness`
as its single dependency. Consequence here: the README and these notes describe a library first, and event-specific material lives outside
this repository. Rejected: building the end project inside this repository.

## D19. Naming of the project, package and repository
The project and GitHub repository are **TinyHarness**; the Python distribution, import package and command are `tinyharness` (Python convention:
lowercase). The README states this once. The local checkout folder is `TinyHarness`. GitHub keeps redirects from the old lowercase repository name.

## D20. Releases are built from a tag by a workflow
A tag `v<version>` runs `.github/workflows/release.yml`: it refuses a tag that differs from the version in `pyproject.toml`, builds the sdist and wheel,
writes `SHA256SUMS`, takes the release notes from the matching `CHANGELOG.md` section, attests build provenance, signs every file keylessly with cosign and
publishes the GitHub release. Running the workflow by hand is a dry run that publishes nothing and keeps the files as an artifact. Nothing is uploaded to PyPI:
the package is installed from the repository or the release files. Rejected: signing with a personal key (a long-lived secret to protect), publishing to PyPI
before the name and the project are settled.

## D21. Branch protection and one required check
The ruleset `protect-main` (same shape as the owner's other repository) needs a pull request and the single check `CI result`, blocks medium and higher CodeQL
findings, and forbids deleting or force-pushing `main`. `CI result` is a final job that fails unless the test and engine jobs succeeded, so the matrix can
change without editing the ruleset.
