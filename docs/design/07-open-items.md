# Open items

## Needs the repository owner (accounts or settings)
- **Codecov**: sign in at codecov.io with GitHub, enable the repository, then add the upload token as the Actions secret
  `CODECOV_TOKEN`. The workflow skips the upload while the secret is absent, so CI stays green. The coverage badge shows
  "unknown" until the first upload.
- **OpenSSF Best Practices badge**: register the project at bestpractices.dev, then add its badge (needs the numeric project id).
- **GitHub Pages**: set Pages to "GitHub Actions" in repository settings so the API reference deploys (the workflow exists).
- **Release badge**: needs a first tagged release.
- **Dependabot security updates**: a repository setting.

## Event-day decisions
- Which problem statement to take (see `docs/PROBLEMS.md` for sixteen guesses, `docs/PITCH.md` for the demo outline).
- Whether demos start at 17:15 or 17:30.
- Rehearse with `--offline`; keep a recording of the working demo.

## Technical follow-ups, none started
- Time the tiers on a low-end laptop, an Apple-silicon Mac and a Windows arm64 machine.
- Try Gemma 4 E4B on a 6 GB GPU (the file is 4.6 GB plus a projector, so it may not fit with a long context).
- Audio input and speech (check what the chosen model and engine support first).
- Embedding-based retrieval behind `tools.search`.
- Streaming for `extract`, `digest` and `ask` (they print at the end).
- Authentication for the web UI if it is ever exposed beyond localhost.
- A `Dockerfile` for problem statement 16 in `docs/PROBLEMS.md`.
- Screenshots or a short recording in the README after a problem statement is chosen.

## Known limitations
- Frontmatter parser is flat; nested YAML in `SKILL.md` is ignored.
- `fetch_url` does not block private addresses.
- The web UI has no authentication and is single-user in spirit (conversations are separated per tab only).
- The character-based context budget is approximate.
