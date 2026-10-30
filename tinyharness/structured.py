"""@file structured.py
@brief Get validated JSON out of a model: schema check, error feedback, retry, CSV export.

Small models often add chatter or miss a key. Rather than hoping, ask_json
extracts the first JSON value from the reply, validates it against a flat
schema, and on failure sends the exact error back to the model and tries again.
Powers the `extract` command (receipt photo to CSV, and similar).
"""
import csv
import io
import json

TYPES = {"str": str, "int": int, "float": (int, float), "bool": bool, "list": list, "dict": dict}


def find_json(text):
    """@brief Find the first valid JSON object or array inside text (code fences and chatter allowed).

    @param text Model reply.
    @return The parsed value.
    @throws ValueError If nothing parses.
    """
    dec = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch in "{[":
            try:
                return dec.raw_decode(text[i:])[0]
            except ValueError:
                continue
    raise ValueError("no JSON found in the reply")


def check(obj, schema):
    """@brief Validate one object against a flat schema.

    Booleans are rejected where a number is expected (in Python, True is an int).

    @param obj Parsed value.
    @param schema Mapping field name -> one of `str int float bool list dict`.
    @throws ValueError Describing the first problem (not an object, missing key, wrong type).
    """
    if not isinstance(obj, dict):
        raise ValueError("expected a JSON object, got " + type(obj).__name__)
    for k, t in schema.items():
        if k not in obj:
            raise ValueError("missing key: " + k)
        ok = isinstance(obj[k], TYPES[t]) and not (t in ("int", "float") and isinstance(obj[k], bool))
        if not ok:
            raise ValueError("key %s should be %s" % (k, t))


def ask_json(client, prompt, schema, images=None, system=None, many=False, retries=2):
    """@brief Ask a model for structured data, validating and retrying.

    @param client A Client.
    @param prompt Instruction or question.
    @param schema Flat schema, see check.
    @param images Optional base64 images (for example a receipt photo).
    @param system Optional extra system text.
    @param many True expects a JSON array of objects, False one object.
    @param retries Extra attempts after the first.
    @return The validated object, or list of objects.
    @throws ValueError If every attempt is invalid.
    """
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
    """@brief Render rows as CSV text with a header from the schema field order.

    @param rows List of dicts.
    @param schema Defines the columns; extra keys in rows are ignored.
    @return CSV with `\n` line endings.
    """
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=list(schema), extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return out.getvalue()
