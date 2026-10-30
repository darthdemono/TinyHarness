## What changed and why

## How you checked it

- [ ] `python -m pytest -q --cov` passes (the suite requires 100 percent line and branch coverage)
- [ ] `ruff check .` and `mypy tinyharness` pass
- [ ] A bug fix has a regression test that fails without the fix
- [ ] New or changed public behaviour is in the README and under Unreleased in `CHANGELOG.md`
- [ ] Docstrings use the Doxygen style used elsewhere in the package
- [ ] No API keys, tokens or personal data in the diff
- [ ] I wrote this change or have the right to submit it under Apache-2.0 ([Developer Certificate of Origin](https://developercertificate.org/))
