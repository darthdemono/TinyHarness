# Working here

## Commands
```
pip install -e ".[dev]"                 # editable install with test and lint tools
python -m pytest -q --cov               # tests plus the 100 percent coverage gate
ruff check .                            # lint
mypy tinyharness                        # types
python -m build                         # sdist and wheel
doxygen Doxyfile                        # API reference into documentation/
tinyharness doctor                      # what this machine can run
```

## Style
- Standard library only. A new dependency needs a strong reason and a decision-log entry.
- Document every module, class and function in Doxygen style (`@brief`, `@param`, `@return`) and explain *why*, not only what.
  Tool functions: short plain first paragraph, tags after a blank line.
- Keep line length at 100 (ruff), Python 3.11 compatible syntax.
- ASCII in source and docs; no emoji.
- Every behaviour change comes with a test written from the intended behaviour. Keep branch coverage at 100 percent.

## Commit messages
One plain sentence of about ten to fifteen words describing the outcome, one `-m` only, no trailers and no body.
Group related files into one commit; aim for a handful of commits per round rather than one per file. Do not stage with `git add .`.
Work on a branch, open a pull request, merge with rebase after the required checks pass.

## Recipes
**Add a tool**: write a function with annotated parameters and a one-sentence docstring, then `agent.tool(fn)` or add it to
`extras.extras()` / `tools.folder_tools()`. Test it with the fake server (`tests/fake_server.py`).

**Add a preset**: one entry in `presets.PRESETS` using `{lang}`; the CLI choices update automatically; add it to the preset test.

**Add a skill**: `tinyharness/skills/<name>/SKILL.md` with frontmatter `name` (equal to the folder) and `description`; run
`tinyharness skills --validate`. Bundled skills are included in the wheel via `pyproject.toml`.

**Add a command**: a subparser in `cli.main`, a branch in `cli.run`, a test in `tests/test_cli_*.py`; update the README command list.

**Point at another model server**: `--backend openai --url http://host:port/v1` (llama.cpp, vLLM, LM Studio, hosted) or
`--backend ollama --url http://host:11434`. Keys: `TINYHARNESS_API_KEY`, or `--unv ENTRY` with an UnENVerse vault.
