"""@file tools.py
@brief Ready-made tools that give a model read access to one folder, and nothing else.

Used for retrieval (the `--docs` flag, the `ask` command and the grounded flow).
Every path is resolved and checked against the root, so `../` and symlinks
cannot reach outside it. Search is plain keyword counting on purpose: no index,
no embeddings, no dependencies, instant on a hack-day sized folder.
"""
import os
import re

TEXT = (".md", ".txt", ".rst", ".csv", ".json", ".toml", ".yaml", ".yml", ".html", ".py", ".js", ".ts", ".rs", ".go", ".java", ".c", ".h", ".cpp")
SKIP = {".git", "node_modules", ".venv", "__pycache__", "dist", "build"}
MAX_READ = 20000


def search(root, query, limit=5):
    """@brief Keyword search under a folder.

    Words shorter than three letters are ignored. A file scores the number of times
    query words occur in it; its best line (most distinct query words) is returned
    with its line number so answers can cite `path:line`.

    @param root Folder to search.
    @param query Free text.
    @param limit Maximum hits.
    @return List of `(score, relative_path, line_number, line_text)`, best first, ties by path.
    """
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
    """@brief Yield relative paths (always with `/`) of text files below root, skipping vendor folders.

    Only extensions in TEXT are listed; folders named in SKIP (.git, node_modules, .venv, ...) are not entered.

    @param root Folder to walk.
    """
    for d, dirs, names in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in SKIP)
        for n in sorted(names):
            if n.endswith(TEXT):
                yield os.path.relpath(os.path.join(d, n), root).replace(os.sep, "/")  # same output on Windows


def folder_tools(root):
    """@brief Create the three folder tools bound to one root.

    @param root Folder the tools may touch.
    @return `[list_files, read_file, search_docs]`, ready for Agent.add_tools.
    """
    root = os.path.realpath(root)

    def inside(rel):
        """@brief Resolve a relative path and refuse anything outside the root.

        @param rel Relative path from the model.
        @return Absolute path inside the root.
        @throws ValueError If the resolved path escapes the root.
        """
        p = os.path.realpath(os.path.join(root, rel))
        if p != root and not p.startswith(root + os.sep):
            raise ValueError("path outside the folder: " + rel)
        return p

    def list_files():
        """List the readable text files in the folder.

        @return One relative path per line, or `no files`.
        """
        return "\n".join(sorted(_walk(root))) or "no files"

    def read_file(path: str):
        """Read a text file from the folder by relative path (first 20000 characters).

        @param path Relative path as listed by list_files.
        @return File text, truncated to keep small context windows usable.
        """
        with open(inside(path), encoding="utf-8", errors="replace") as f:
            return f.read(MAX_READ)

    def search_docs(query: str):
        """Keyword search over the folder. Returns the best 5 hits as path:line: text.

        @param query Words to look for.
        @return Lines of `path:line: text`, or `no matches`.
        """
        hits = search(root, query)
        return "\n".join("%s:%d: %s" % (r, n, t) for _, r, n, t in hits) or "no matches"

    return [list_files, read_file, search_docs]
