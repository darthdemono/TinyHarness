"""Run the same prompts through several models and print a markdown table."""
import time

from .client import Client


def run(models, prompts, **client_args):
    """Return rows (model, prompt, seconds, answer); a failing call is recorded as 'error: ...'."""
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
    out = ["| model | prompt | seconds | answer |", "|---|---|---|---|"]
    for m, p, s, a in rows:
        a = " ".join(a.split())
        a = (a[:width] + "...") if len(a) > width else a
        out.append("| %s | %s | %.2f | %s |" % (m, p.replace("|", "/"), s, a.replace("|", "/")))
    return "\n".join(out)
