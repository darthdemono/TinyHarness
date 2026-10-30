# Contributing

Start with a small, reproducible change. The project supports Python 3.11 and newer and has no runtime dependencies; keep it that way. Run `python -m pytest -q`, `ruff check .` and `mypy tinyharness` before proposing code. Tests use a local fake server, so they need no model and no network.

Do not include API keys, private prompts or personal images in fixtures. Security reports follow [SECURITY.md](SECURITY.md), not a public issue.
