# Contributing

Thanks for helping. Please start with a small, reproducible change. By taking part you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).

## Reporting a bug or asking for a feature

Open an issue from the templates. A bug report needs the output of `tinyharness doctor`, the command you ran and what you expected.
Do not paste API keys. Security problems go through the private form in [SECURITY.md](SECURITY.md), never a public issue.

## Setting up

```
pip install -e ".[dev]"
python -m pytest -q --cov       # tests; the suite requires 100 percent line and branch coverage
ruff check .                    # lint
mypy tinyharness                # types
doxygen Doxyfile                # API reference into documentation/ (optional)
```

The project supports Python 3.11 and newer and has no runtime dependencies. Keep it that way: a new dependency needs a strong reason and a
decision-log entry in [docs/design/03-decision-log.md](docs/design/03-decision-log.md).

## Making a change

1. Branch from `main`. Direct pushes to `main` are not accepted; changes arrive through a pull request that passes the `CI result` check.
2. Write the test from the behaviour you expect, not from the code. A bug fix needs a regression test that fails without the fix.
3. Document every module, class and function in the Doxygen style used in the package (`@brief`, `@param`, `@return`), and explain why, not
   only what. A tool function's docstring starts with one short plain sentence: it is sent to the model.
4. A user-visible change adds a line under Unreleased in [CHANGELOG.md](CHANGELOG.md), and the README changes with it.
5. Commit messages are one plain sentence of about ten to fifteen words describing the outcome. Group related files into one commit.

## Developer Certificate of Origin

Contributions are made under Apache-2.0. The pull request template has a checkbox in which you confirm you wrote the change or have the
right to submit it, as described by the [Developer Certificate of Origin](https://developercertificate.org/). `Signed-off-by` lines are
welcome but not required.

## Dependencies

Dependabot proposes weekly updates for GitHub Actions and development tools. Every action in a workflow is pinned to a commit hash with the
release in a comment. The dependency review workflow checks pull requests that change dependencies.

## Where things are

[docs/design/INDEX.md](docs/design/INDEX.md) lists the design notes: architecture, decisions, history, evidence and traps.
