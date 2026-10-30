"""Ask for JSON that matches a flat schema, validate it, retry with the error as feedback."""
import csv
import io
import json

TYPES = {"str": str, "int": int, "float": (int, float), "bool": bool, "list": list, "dict": dict}


def find_json(text):
    """Return the first JSON object or array embedded in text (fences and chatter tolerated)."""
    dec = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch in "{[":
            try:
                return dec.raw_decode(text[i:])[0]
            except ValueError:
                continue
    raise ValueError("no JSON found in the reply")


def check(obj, schema):
    """Raise ValueError unless obj is a dict with every schema key at the right type."""
    if not isinstance(obj, dict):
        raise ValueError("expected a JSON object, got " + type(obj).__name__)
    for k, t in schema.items():
        if k not in obj:
            raise ValueError("missing key: " + k)
        ok = isinstance(obj[k], TYPES[t]) and not (t in ("int", "float") and isinstance(obj[k], bool))
        if not ok:
            raise ValueError("key %s should be %s" % (k, t))


def ask_json(client, prompt, schema, images=None, system=None, many=False, retries=2):
    """Return one dict matching schema, or a list of them when many=True."""
    shape = json.dumps({k: t for k, t in schema.items()})
    want = "a JSON array of objects" if many else "one JSON object"
    msgs = [{"role": "system", "content": (system or "") + "\nReply with %s shaped like %s and nothing else." % (want, shape)}]
    msgs.append({"role": "user", "content": prompt, **({"images": images} if images else {})})
    err = None
    for _ in range(retries + 1):
        reply = client.chat(msgs)["content"]
        try:
            obj = find_json(reply)
            for row in obj if many and isinstance(obj, list) else [obj]:
                check(row, schema)
            if many and not isinstance(obj, list):
                raise ValueError("expected a JSON array")
            return obj
        except ValueError as e:
            err = e
            msgs += [{"role": "assistant", "content": reply},
                     {"role": "user", "content": "That was invalid: %s. Reply again with only the JSON." % e}]
    raise ValueError("no valid JSON after %d tries: %s" % (retries + 1, err))


def to_csv(rows, schema):
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=list(schema), extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return out.getvalue()
