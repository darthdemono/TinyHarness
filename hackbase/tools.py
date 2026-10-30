"""Ready-made tools over a local folder: list, read and keyword search. Sandboxed to the root."""
import os
import re

TEXT = (".md", ".txt", ".rst", ".csv", ".json", ".py")
MAX_READ = 20000


def folder_tools(root):
    """Return [list_files, read_file, search_docs] bound to root; paths cannot escape it."""
    root = os.path.realpath(root)

    def inside(rel):
        p = os.path.realpath(os.path.join(root, rel))
        if p != root and not p.startswith(root + os.sep):
            raise ValueError("path outside the folder: " + rel)
        return p

    def walk():
        for d, _, names in os.walk(root):
            for n in sorted(names):
                if n.endswith(TEXT):
                    yield os.path.relpath(os.path.join(d, n), root)

    def list_files():
        """List the readable text files in the folder."""
        return "\n".join(sorted(walk())) or "no files"

    def read_file(path: str):
        """Read a text file from the folder by relative path (first 20000 characters)."""
        with open(inside(path), encoding="utf-8", errors="replace") as f:
            return f.read(MAX_READ)

    def search_docs(query: str):
        """Keyword search over the folder. Returns the best 5 files with a matching line each."""
        words = [w for w in re.findall(r"\w+", query.lower()) if len(w) > 2]
        hits = []
        for rel in walk():
            with open(inside(rel), encoding="utf-8", errors="replace") as f:
                lines = f.read().splitlines()
            score = sum(ln.lower().count(w) for ln in lines for w in words)
            if score:
                best = max(lines, key=lambda ln: sum(w in ln.lower() for w in words))
                hits.append((score, rel, best.strip()[:200]))
        hits.sort(key=lambda h: (-h[0], h[1]))
        return "\n".join("%s: %s" % (r, s) for _, r, s in hits[:5]) or "no matches"

    return [list_files, read_file, search_docs]
