"""Ready-made multi-call flows: map-reduce digest of long text, and grounded answers with citations."""
import os

from .tools import search

REFUSAL = "That is not covered by the provided material."


def chunks(text, size=6000):
    """Split text on line boundaries into pieces of at most size characters (long lines are cut)."""
    out, cur = [], ""
    for line in text.splitlines():
        while len(line) > size:
            if cur:
                out.append(cur)
                cur = ""
            out.append(line[:size])
            line = line[size:]
        if len(cur) + len(line) + 1 > size and cur:
            out.append(cur)
            cur = ""
        cur += line + "\n"
    return out + ([cur] if cur.strip() else [])


def digest(client, text, instruction="Summarise the key points as short bullets.", size=6000):
    """Map each chunk through the instruction, then reduce the partials until one answer fits."""
    parts = [client.ask("%s\n\n%s" % (instruction, c)) for c in chunks(text, size)]
    while len(parts) > 1:
        merged = chunks("\n\n".join(parts), size)
        if len(merged) >= len(parts):  # partials are not shrinking; stop instead of looping forever
            break
        parts = [client.ask("Combine these notes. %s\n\n%s" % (instruction, c)) for c in merged]
    return client.ask("Combine into one final answer. %s\n\n%s" % (instruction, "\n\n".join(parts))) if len(parts) > 1 else (parts[0] if parts else "")


def grounded(client, question, root, system="", window=2):
    """Answer only from files under root. Return (answer, ['path:line', ...]); refuse without calling the model if nothing matches."""
    hits = search(root, question)
    if not hits:
        return REFUSAL, []
    ctx, srcs = [], []
    for _, rel, n, _ in hits:
        with open(os.path.join(root, rel), encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
        lo = max(0, n - 1 - window)
        ctx.append("[%s:%d]\n%s" % (rel, n, "\n".join(lines[lo:n + window])))
        srcs.append("%s:%d" % (rel, n))
    sys_msg = (system + "\n" if system else "") + (
        "Answer using ONLY the sources. Cite as [path:line]. If they do not contain the answer, reply exactly: " + REFUSAL
    )
    return client.ask("Sources:\n\n%s\n\nQuestion: %s" % ("\n\n".join(ctx), question), system=sys_msg), srcs
