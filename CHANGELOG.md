# Changelog

All notable changes are listed here, newest first. The format follows [Keep a Changelog](https://keepachangelog.com/). There is no tagged
release yet, so everything is under Unreleased.

## Unreleased

### Added
- Model client for llama.cpp, Ollama and any OpenAI-compatible server, with image input and token streaming.
- Tool-calling agent loop with native tool calls, a JSON-text mode for models without them, context trimming and tool-output limits.
- llama.cpp manager: download with SHA-256 check for Linux, macOS and Windows on x64 and arm64, CPU or Vulkan GPU, offline mode, hardware check.
- Folder tools, calculator, clock and web page text tools; Agent Skills loader and validator with eight bundled skills.
- Structured JSON extraction, long-text digest, grounded answers with citations, role presets and saved sessions.
- Prompt-injection sweep, model comparison table, one-page streaming web chat.
- `tinyharness new` writes a fresh project that depends on TinyHarness.
- UnENVerse vault support: `--unv` and `--unv-pool` inject API keys without printing them.
- Doxygen API reference, design notes under `docs/design`, 100 percent test coverage gate, CI on six platforms, CodeQL, OpenSSF Scorecard.
