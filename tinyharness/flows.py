"""@file flows.py
@brief Reusable multi-call behaviours: digest long text, and answer only from given sources.

Both exist because small local models have small context windows and tend to
invent facts. digest splits and recombines. grounded retrieves first, answers
second, cites where each fact came from, and refuses without calling the model
when retrieval finds nothing.
"""
import os

from .tools import search

REFUSAL = "That is not covered by the provided material."


def chunks(text, size=6000):
    """@brief Split text into pieces of at most `size` characters on line boundaries (over-long lines are cut).

    @param text Text to split.
    @param size Maximum piece length.
    @return List of pieces; empty for blank text.
    """
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
    """@brief Map-reduce summary of text that does not fit in one prompt.

    Each chunk is processed with the instruction, then the partial results are
    combined in rounds while that makes the list shorter. If combining stops
    shrinking the list (answers longer than the chunk size), it stops and does one
    final combine instead of looping forever.

    @param client A Client.
    @param text Input text.
    @param instruction What to do with each piece.
    @param size Chunk size in characters.
    @return The final text, or an empty string for empty input.
    """
    parts = [client.ask("%s\n\n%s" % (instruction, c)) for c in chunks(text, size)]
    while len(parts) > 1:
        merged = chunks("\n\n".join(parts), size)
        if len(merged) >= len(parts):  # partials are not shrinking; stop instead of looping forever
            break
        parts = [client.ask("Combine these notes. %s\n\n%s" % (instruction, c)) for c in merged]
    return client.ask("Combine into one final answer. %s\n\n%s" % (instruction, "\n\n".join(parts))) if len(parts) > 1 else (parts[0] if parts else "")


def grounded(client, question, root, system="", window=2):
    """@brief Answer a question using only the files under a folder, with citations.

    Retrieval is keyword search (tools.search). The model sees the matching passages
    (a few lines around each hit) labelled `[path:line]` and is told to cite them and
    to reply with a fixed refusal sentence if the sources do not contain the answer.
    With no hits at all the refusal is returned and the model is never called.

    @param client A Client.
    @param question The question.
    @param root Folder of source files.
    @param system Optional extra system text.
    @param window Lines of context before and after each hit.
    @return `(answer, ["path:line", ...])`.
    """
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
