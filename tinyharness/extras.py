"""General-purpose tools any project can hand to the agent: calculator, clock, web page text."""
import ast
import datetime
import html.parser
import operator
import urllib.request

_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}


def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        a, b = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(b) > 100:
            raise ValueError("exponent too large")
        return _OPS[type(node.op)](a, b)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("only numbers and + - * / // % ** are allowed")


def calculator(expression: str):
    """Evaluate an arithmetic expression such as (3 + 4) * 2.5. Use it for any maths instead of guessing."""
    return _eval(ast.parse(expression.strip(), mode="eval").body)


def now():
    """Return the current local date and time."""
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


class _Text(html.parser.HTMLParser):
    SKIP = {"script", "style", "noscript", "svg"}

    def __init__(self):
        super().__init__()
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        self.skip += tag in self.SKIP

    def handle_endtag(self, tag):
        self.skip -= tag in self.SKIP and self.skip > 0

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.out.append(data.strip())


def page_text(raw):
    """Visible text of an HTML document, one chunk per line."""
    p = _Text()
    p.feed(raw)
    return "\n".join(p.out)


def fetch_url(url: str):
    """Download a web page (http or https only) and return its readable text, at most 6000 characters."""
    if not url.startswith(("http://", "https://")):
        raise ValueError("only http and https URLs are allowed")
    req = urllib.request.Request(url, headers={"User-Agent": "tinyharness"})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read(2_000_000).decode(r.headers.get_content_charset() or "utf-8", errors="replace")
    text = page_text(raw) if "html" in (r.headers.get_content_type() or "") else raw
    return text[:6000]


def extras():
    return [calculator, now, fetch_url]
