"""Ready-made tools over a local folder: list, read and keyword search. Sandboxed to the root."""
import os
import re

TEXT = (".md", ".txt", ".rst", ".csv", ".json", ".toml", ".yaml", ".yml", ".html", ".py", ".js", ".ts", ".rs", ".go", ".java", ".c", ".h", ".cpp")
SKIP = {".git", "node_modules", ".venv", "__pycache__", "dist", "build"}
MAX_READ = 20000


def search(root, query, limit=5):
    """Keyword search under root. Return up to limit (score, path, line_no, line) hits, best first."""
    root = os.path.realpath(root)
    words = [w for w in re.findall(r"\w+", query.lower()) if len(w) > 2]
    hits = []
    for rel in _walk(root):
        with open(os.path.join(root, rel), encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
        score = sum(ln.lower().count(w) for ln in lines for w in words)
        if score:
            n, best = max(enumerate(lines, 1), key=lambda x: sum(w in x[1].lower() for w in words))
            hits.append((score, rel, n, best.strip()[:200]))
    hits.sort(key=lambda h: (-h[0], h[1]))
    return hits[:limit]


def _walk(root):
    for d, dirs, names in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in SKIP)
        for n in sorted(names):
            if n.endswith(TEXT):
                yield os.path.relpath(os.path.join(d, n), root).replace(os.sep, "/")  # same output on Windows


def folder_tools(root):
    """Return [list_files, read_file, search_docs] bound to root; paths cannot escape it."""
    root = os.path.realpath(root)

    def inside(rel):
        p = os.path.realpath(os.path.join(root, rel))
        if p != root and not p.startswith(root + os.sep):
            raise ValueError("path outside the folder: " + rel)
        return p

    def list_files():
        """List the readable text files in the folder."""
        return "\n".join(sorted(_walk(root))) or "no files"

    def read_file(path: str):
        """Read a text file from the folder by relative path (first 20000 characters)."""
        with open(inside(path), encoding="utf-8", errors="replace") as f:
            return f.read(MAX_READ)

    def search_docs(query: str):
        """Keyword search over the folder. Returns the best 5 hits as path:line: text."""
        hits = search(root, query)
        return "\n".join("%s:%d: %s" % (r, n, t) for _, r, n, t in hits) or "no matches"

    return [list_files, read_file, search_docs]
