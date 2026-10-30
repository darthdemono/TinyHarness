"""@file bench.py
@brief Compare models: run the same prompts through each and tabulate time and answers.
"""
import time

from .client import Client


def run(models, prompts, **client_args):
    """@brief Ask every model every prompt.

    A model that fails (not pulled, server down) is recorded as an `error: ...`
    answer so the rest of the comparison still completes.

    @param models Model names to compare.
    @param prompts Questions to ask each model.
    @param client_args Passed to Client (backend, base_url, api_key).
    @return List of `(model, prompt, seconds, answer)`.
    """
    rows = []
    for m in models:
        c = Client(model=m, **client_args)
        for p in prompts:
            t = time.perf_counter()
            try:
                ans = c.ask(p)
            except Exception as e:  # one dead model must not stop the comparison
                ans = "error: %s" % e
            rows.append((m, p, time.perf_counter() - t, ans))
    return rows


def table(rows, width=80):
    """@brief Format results as a Markdown table.

    Answers are flattened to one line and cut to a width; the pipe character is replaced so cells stay intact.

    @param rows Output of run.
    @param width Longest answer shown.
    @return Markdown text.
    """
    out = ["| model | prompt | seconds | answer |", "|---|---|---|---|"]
    for m, p, s, a in rows:
        a = " ".join(a.split())
        a = (a[:width] + "...") if len(a) > width else a
        out.append("| %s | %s | %.2f | %s |" % (m, p.replace("|", "/"), s, a.replace("|", "/")))
    return "\n".join(out)
