# Security policy

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability or disclose secrets in an issue. Use
[GitHub's private vulnerability-reporting form](https://github.com/darthdemono/TinyHarness/security/advisories/new) for this repository,
or contact the maintainer through the email address on the [GitHub profile](https://github.com/darthdemono).

Include a minimal reproduction, the affected version, the impact, and any proposed mitigation. Use invented data and never include real
API keys.

### Security contacts

The maintainer, Jubair Hasan ([\@darthdemono](https://github.com/darthdemono)), is the only security contact. The private form above
reaches the maintainer directly.

### What to expect

- Reports are acknowledged within seven days.
- The maintainer confirms or rejects the report, then works with the reporter on a fix and a disclosure date. The reporter is credited
  unless they prefer not to be.
- Once a fix is released, the vulnerability is published as a
  [GitHub Security Advisory](https://github.com/darthdemono/TinyHarness/security/advisories), with a CVE where one applies. It names the
  affected versions, how to tell if you are affected, and the fixed version or the mitigation.
- Please keep the report private until a fix ships or 90 days have passed, whichever comes first. There is no bug bounty and no PGP key:
  the private form is encrypted in transit and visible only to the maintainer.

### Safe harbour

Good-faith research that follows this policy is welcome. The maintainer will not start legal action over it, provided you stay within the
scope below, use only systems you own or are authorised to test, do not read, change or destroy other people's data, and stop and report
if you reach real secrets.

### How reports are handled

1. Acknowledge the report (within seven days) and say what happens next.
2. Record it in a private advisory draft, reproduce it, and rate its impact.
3. Fix it, with a regression test that fails without the fix.
4. Verify the fix with the reporter before the release.
5. Release, publish the advisory, and credit the reporter.

### Security incidents

Incidents without a direct exploit (a compromised dependency, a tampered workflow, a leaked token) are handled the same way: the maintainer
confirms the incident, revokes and rotates what was exposed, and publishes an advisory that says who is affected and what to do.

## Scope

In scope: the Python package and command, the local web page, the llama.cpp download and verification code, and the project template.
Things worth knowing about the design:

- The web page has no authentication and listens on 127.0.0.1 only. Exposing it on a network is outside the supported use.
- `fetch_url` and the folder tools are for the user's own agent; the folder tools cannot read outside the folder they are given.
- The engine download is checked against the SHA-256 digest published with each release asset before anything is unpacked, and archives
  with unsafe paths are refused.
- API keys are read from the environment or injected by an UnENVerse vault and are never printed or placed on a command line.

## Supported versions

Only the latest release receives security fixes. There is no tagged release yet; until there is one, the `main` branch is the supported version.

## Secrets and credentials used by the project

- The project's only credential is the coverage upload token. It lives only as a GitHub Actions secret, is never committed or printed,
  and workflows triggered by forks do not receive it.
- The project publishes no signing keys and no packages that need one.
- GitHub secret scanning and push protection should stay on; `.gitignore` excludes environment files; test data must not look like real
  credentials.

## Dependency vulnerability policy

- TinyHarness has no runtime dependencies (standard library only). Development tools and GitHub Actions are updated by Dependabot weekly,
  with a seven-day cooldown, and every action is pinned to a commit hash.
- The dependency graph is enabled, and pull requests are checked by the dependency review workflow.
- Threshold: a known vulnerability in a dependency that ships or runs in CI at high severity or above is fixed by upgrading or replacing
  it before the next release. If it does not affect TinyHarness, the reason is written down in the pull request that dismisses it.

## Static analysis policy

- CodeQL (Python) runs on every push, pull request and weekly; OpenSSF Scorecard runs on every push to `main` and weekly; ruff and mypy run
  in CI.
- Threshold: any CodeQL finding of medium severity or higher is fixed, or dismissed with a written reason, before the next release.

## Fuzzing and audits

There is no fuzzing yet. Parsers that read untrusted text (`find_json`, the skill frontmatter parser, the stream readers) are covered by
behaviour tests with malformed input. No independent audit has been done.
