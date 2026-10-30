# Threat model

TinyHarness is a library and command line that runs on a user's own machine and talks to a language model. This note lists what it
protects, who might attack it, where trust changes, and what it does and does not defend against. It is a short working model, not an audit.

## What is protected

- **API keys** for hosted model services (read from the environment or injected by an UnENVerse vault).
- **Files the user points it at** (`--docs`, `ask`, `digest`): they must not be readable outside the chosen folder.
- **The user's machine**: downloading and running a native engine must not run something other than the official release.
- **The user's conversation**: it stays on the machine; nothing is sent anywhere except to the model server the user chose.

## Actors

| Actor | Can do | Trusted? |
|---|---|---|
| The user running the command | Everything the process can do | Yes |
| The model (and anything it was told to read) | Choose tool calls and arguments, produce text | No: its output is treated as untrusted input |
| A web page or file the agent reads | Contain instructions aimed at the model (prompt injection) | No |
| A person who can reach the local web page | Chat with the agent, use its tools | Only the local user; the page binds to 127.0.0.1 and has no login |
| GitHub and the model host | Serve releases and answers | Over TLS; release files are checked against the published SHA-256 |
| A contributor | Propose changes by pull request | Reviewed by the maintainer; CI runs without secrets for forks |

## Trust boundaries and controls

1. **Model to tools.** Tool arguments come from the model. Folder tools resolve every path and refuse anything outside the root; the
   calculator evaluates only arithmetic from a parsed expression and never calls `eval`; `fetch_url` accepts only http and https and caps
   size; a tool that raises is reported back to the model instead of crashing the run; tool output is truncated.
2. **Engine download.** The release list comes from the GitHub API over TLS. The archive is hashed and compared with the digest GitHub
   publishes for that asset before unpacking, and every archive member path is checked so nothing lands outside the destination.
3. **Secrets.** Keys are never printed or placed on a command line; `--unv` injects them into the child environment through UnENVerse.
   Workflows for forks receive no secrets, and the only secret is the coverage upload token.
4. **Local web page.** Binds to 127.0.0.1, serves one HTML page and one POST route, keeps one conversation per browser tab, and has no login.

## Known weaknesses (not defended against)

- **Prompt injection** can make the model misuse the tools it was given. `tinyharness redteam` measures one narrow case (leaking a planted
  string); it is not a guarantee. Give an agent only the tools it needs.
- **`fetch_url` does not block private addresses**, so an injected instruction could make it read a service on the local network.
- **The web page has no authentication.** Do not expose it beyond localhost.
- **A model server the user points at is trusted** with the whole conversation, including images and any tool output.
- **No fuzzing and no independent audit** have been done.

## Review

This model is revisited whenever the attack surface changes: a new tool that touches the network or the file system, a new download, a new
network route. See [SECURITY.md](SECURITY.md) for reporting and [docs/design/03-decision-log.md](docs/design/03-decision-log.md) for design
choices.
