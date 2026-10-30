# Governance

TinyHarness is maintained by one person. This file says who has access to what, what each role is
responsible for, and how that access is granted.

## Members with access to sensitive resources

| Who | Role | Sensitive resources |
|---|---|---|
| Jubair Hasan ([\@darthdemono](https://github.com/darthdemono)) | Maintainer | Repository admin, GitHub Actions secrets (the coverage upload token), repository settings, private vulnerability reports |

There are no other collaborators with write access. The project publishes no signing keys.

## Roles and responsibilities

- **Maintainer.** Reviews and merges changes, triages issues, answers vulnerability reports within the time in
  [SECURITY.md](SECURITY.md), keeps the secrets listed above safe, and decides who else gets access.
- **Contributor.** Anyone who sends a pull request or a patch. Follows [CONTRIBUTING.md](CONTRIBUTING.md). Has no special access.
- **Reporter.** Anyone who opens an issue or a private vulnerability report.

## Granting access

- New collaborators start with read or triage access. Write access is granted only after the maintainer has reviewed a series of
  that person's contributions and is satisfied with their care and judgement. Admin access, and access to any secret, is not
  delegated while the project has a single maintainer.
- Every account with write access or above must use two-factor authentication on GitHub.
- Access is reviewed regularly and removed when no longer needed.

## Decisions

The maintainer decides. Significant design choices are written down, with the options that lost, in
[docs/design/03-decision-log.md](docs/design/03-decision-log.md).

## Legal

Contributions are made under the project licence, Apache-2.0, as described in section 5 of that licence and in GitHub's Terms of
Service (contributions to a repository are licensed under the repository's licence). By opening a pull request you confirm you
have the right to contribute the work.
