# Open items

## Needs the repository owner (accounts or settings)
- **Codecov**: sign in at codecov.io with GitHub, enable the repository, then add the upload token as the Actions secret
  `CODECOV_TOKEN`. The workflow skips the upload while the secret is absent, so CI stays green. The coverage badge shows
  "unknown" until the first upload.
- **OpenSSF Best Practices**: the passing badge is earned (project 16103) and shown in the README. Silver and gold are not attempted.
- **GitHub Pages**: set Pages to "GitHub Actions" in repository settings so the API reference deploys (the workflow exists).
- **Dependabot security updates**: a repository setting.

## Technical follow-ups, none started
- Time the tiers on a low-end laptop, an Apple-silicon Mac and a Windows arm64 machine.
- Try Gemma 4 E4B on a 6 GB GPU (the file is 4.6 GB plus a projector, so it may not fit with a long context).
- Audio input and speech (check what the chosen model and engine support first).
- Embedding-based retrieval behind `tools.search`.
- Streaming for `extract`, `digest` and `ask` (they print at the end).
- Authentication for the web UI if it is ever exposed beyond localhost.
- A `Dockerfile` so a project built on TinyHarness can be shipped and run with one command.
- Screenshots or a short recording in the README.

## Known limitations
- Frontmatter parser is flat; nested YAML in `SKILL.md` is ignored.
- `fetch_url` does not block private addresses.
- The web UI has no authentication and is single-user in spirit (conversations are separated per tab only).
- The character-based context budget is approximate.
